# バイトコード拡張案の分析: 5x32 vs 64bit vs 現状維持

## 概要

ユーザーからの技術的異議を受けて、3つのアプローチを比較検討します:

1. **現状維持 (4x32)**: `[op, v, a, s]` - 4整数 x 32ビット
2. **5x32拡張**: `[op, v, s, a_low, a_high]` - 5整数 x 32ビット
3. **64bit拡張**: `[op, v, a64, s]` - aのみ64ビット

---

## 1. ユーザーの懸念点 (正当性の評価)

### 1.1 `v` への Color Filter 移動の問題

| 懸念 | 評価 | 理由 |
|-----|------|------|
| Card ID > 65535 での破損 | ✅ **正当** | プロモカード等で ID が 70050+ になる可能性あり |
| AI学習の複雑化 | ✅ **正当** | 「opcode が X の場合は v から色を探す」という条件分岐は NN に負担 |

### 1.2 Assembly-Style Unrolling の問題

| 懸念 | 評価 | 理由 |
|-----|------|------|
| MCTS深度爆発 | ✅ **正当** | 1効果 = 3-4ステップ は状態空間を不必要に拡大 |
| 部分状態の探索 | ✅ **正当** | 「フィルタ済みだが選択未完了」の中間状態が増加 |

### 1.3 拡張性の欠如

| 懸念 | 評価 | 理由 |
|-----|------|------|
| 将来のメカニクス対応 | ✅ **正当** | 学年フィルタ、ブレードサイズ等の新規フィルタで即座に限界 |

---

## 2. パフォーマンス影響の分析

### 2.1 Rust での影響

#### 現状 (4x32)
```rust
// bytecode: Vec<i32>
for chunk in bytecode.chunks(4) {
    let (op, v, a, s) = (chunk[0], chunk[1], chunk[2], chunk[3]);
    // 処理
}
```

#### 5x32拡張
```rust
// bytecode: Vec<i32>
for chunk in bytecode.chunks(5) {
    let (op, v, s, a_low, a_high) = (chunk[0], chunk[1], chunk[2], chunk[3], chunk[4]);
    let a = ((a_high as u64) << 32) | (a_low as u64);
    // 処理
}
```

**影響**:
- メモリ: **+25%** 増加
- キャッシュミス率: 若干増加 (1命令あたり 20bytes → 25bytes)
- CPUサイクル: ほぼ変わらず (ビットシフトは高速)

#### 64bit拡張
```rust
// bytecode: Vec<i64> または混合型
for chunk in bytecode.chunks(4) {
    let (op, v, a, s) = (chunk[0] as i32, chunk[1] as i32, chunk[2], chunk[3] as i32);
    // a は i64
}
```

**影響**:
- メモリ: **+25%** 増加 (4x32=128bit → 2x32+1x64+1x32=160bit)
- キャッシュミス率: 若干増加
- CPUサイクル: ほぼ変わらず (64bit演算は現代CPUで高速)

### 2.2 WGSL (GPU) での影響

#### 現状 (4x32)
```wgsl
@group(0) @binding(2) var<storage, read> bytecode: array<i32>;

fn get_instruction(ip: u32) -> vec4<i32> {
    return vec4<i32>(
        bytecode[ip],
        bytecode[ip + 1u],
        bytecode[ip + 2u],
        bytecode[ip + 3u]
    );
}
```

#### 5x32拡張
```wgsl
@group(0) @binding(2) var<storage, read> bytecode: array<i32>;

fn get_instruction(ip: u32) -> vec5<i32> {  // vec5 は存在しない!
    // WGSL には vec5 がないため、個別にロードが必要
    let op = bytecode[ip];
    let v = bytecode[ip + 1u];
    let s = bytecode[ip + 2u];
    let a_lo = bytecode[ip + 3u];
    let a_hi = bytecode[ip + 4u];
    let a = (u32(a_lo) | (u32(a_hi) << 32u));  // u64 として結合
    // ...
}
```

**影響**:
- **重大**: WGSL に `vec5` が存在しないため、個別ロードが必要
- メモリアクセス: 5回/命令 (現状は4回)
- レジスタ圧力: 若干増加

#### 64bit拡張
```wgsl
@group(0) @binding(2) var<storage, read> bytecode: array<i64>;  // または混合

fn get_instruction(ip: u32) -> vec4<i64> {  // 一部が i64
    // WGSL は型統一が必要
    return vec4<i64>(
        bytecode[ip],
        bytecode[ip + 1u],
        bytecode[ip + 2u],
        bytecode[ip + 3u]
    );
}
```

**影響**:
- WGSL は `array<i64>` をサポート
- ただし、`op`, `v`, `s` も 64bit になるためメモリ無駄
- 混合型は WGSL で複雑化

---

## 3. 推奨アプローチ: 5x32 拡張

### 3.1 理由

| 基準 | 4x32 (現状) | 5x32 | 64bit |
|-----|-------------|------|-------|
| メモリ効率 | ✅ 最良 | 🟡 +25% | 🟡 +25% |
| WGSL互換性 | ✅ 最良 | 🟡 個別ロード必要 | 🟡 型統一必要 |
| 拡張性 | ❌ 不十分 | ✅ 64bit属性 | ✅ 64bit属性 |
| AI学習 | ❌ 複雑な条件 | ✅ クリーン | ✅ クリーン |
| 実装コスト | - | 🟡 中程度 | 🔴 高い |

### 3.2 新しいレイアウト (5x32)

```
[op, v, s, a_low, a_high]

op (i32): Opcode
v  (i32): Value/Count (16bit) + Color Mask (6bit) + Flags (10bit)
s  (i32): Slot/Zone (24bit) + Flags (8bit)
a  (i64): Attribute Filter (64bit完全使用可能)
```

### 3.3 64bit `a` ワードの新しいレイアウト

```
┌─────────────────────────────────────────────────────────────────┐
│ Bit  0     : IS_OPTIONAL                                       │
│ Bit  1     : DYNAMIC_VALUE                                     │
│ Bits 2-3   : Card Type (0=Any, 1=Member, 2=Live)               │
│ Bits 4-7   : Group ID (4 bits = 16 groups)                     │
│ Bits 8-12  : Unit ID (5 bits = 32 units)                       │
│ Bits 13-17 : Cost Threshold (5 bits = 0-31)                    │
│ Bit  18    : Cost Mode (0=GE, 1=LE)                            │
│ Bit  19    : Tapped Filter                                     │
│ Bit  20    : Has Blade Heart                                   │
│ Bit  21    : Not Has Blade Heart                               │
│ Bits 22-28 : Color Mask (7 bits = 7 colors)                    │
│ Bits 29-35 : Character ID 1 (7 bits = 128 chars)               │
│ Bits 36-42 : Character ID 2 (7 bits)                           │
│ Bits 43-49 : Character ID 3 (7 bits)                           │
│ Bits 50-56 : Special Filter ID (7 bits)                        │
│ Bits 57-63 : Reserved for future use                           │
└─────────────────────────────────────────────────────────────────┘
```

**改善点**:
- Color Mask が `a` 内に配置 (v から分離)
- Character ID が 64bit 内に収まる (切り捨て問題解決)
- 将来の拡張用に 7ビット予備

---

## 4. 実装ステップ

### Phase 1: Rust インタープリタの更新

1. **バイトコードストレージの変更**
   ```rust
   // Before
   pub bytecode: Vec<i32>

   // After
   pub bytecode: Vec<i32>  // 5要素ごとに1命令
   ```

2. **チャンク処理の変更**
   ```rust
   // Before
   for chunk in bytecode.chunks(4) { ... }

   // After
   for chunk in bytecode.chunks(5) {
       let op = chunk[0];
       let v = chunk[1];
       let s = chunk[2];
       let a = if chunk.len() >= 5 {
           ((chunk[4] as u64) << 32) | (chunk[3] as u64)
       } else { 0 };
       // ...
   }
   ```

### Phase 2: Python コンパイラの更新

1. **`compile()` メソッドの変更**
   ```python
   def compile(self) -> List[int]:
       bytecode = []
       # ... 既存のロジック ...
       # 各命令に a_high を追加
       for i in range(0, len(bytecode), 4):
           a = bytecode[i+2]
           a_low = a & 0xFFFFFFFF
           a_high = (a >> 32) & 0xFFFFFFFF
           bytecode[i+2] = a_low
           bytecode.insert(i+3, a_high)
       return bytecode
   ```

### Phase 3: WGSL シェーダーの更新

1. **命令読み込みの変更**
   ```wgsl
   fn get_instruction(ip: u32) -> (i32, i32, i32, u64) {
       let op = bytecode[ip];
       let v = bytecode[ip + 1u];
       let s = bytecode[ip + 2u];
       let a_lo = bytecode[ip + 3u];
       let a_hi = bytecode[ip + 4u];
       let a = (u32(a_lo) | (u32(a_hi) << 32u));
       return (op, v, s, a);
   }
   ```

---

## 5. パフォーマンス予測

### 5.1 メモリ使用量

| 項目 | 現状 (4x32) | 5x32 | 増加率 |
|-----|-------------|------|-------|
| 1命令あたり | 16 bytes | 20 bytes | +25% |
| 全カードのバイトコード | ~1.5 MB | ~1.9 MB | +25% |
| GPU VRAM | ~2 MB | ~2.5 MB | +25% |

### 5.2 実行速度

| 環境 | 予測影響 |
|-----|---------|
| Rust (CPU) | < 1% 遅延 (メモリ帯域幅依存) |
| WGSL (GPU) | 1-3% 遅延 (メモリアクセス増加) |
| AI訓練 | **改善** (状態空間の削減) |

### 5.3 AI訓練への影響

| 側面 | 影響 |
|-----|------|
| 状態空間 | **削減** (Unrolling回避) |
| MCTS深度 | **削減** (1効果 = 1ステップ) |
| NN入力エンコーディング | **簡素化** (レジスタ意味が明確) |

---

## 6. 結論

**推奨**: 5x32 拡張アプローチ

**理由**:
1. 64bit 属性フィルタで全ての情報を1命令に収容
2. AI訓練にとって最適 (状態空間削減)
3. 実装コストが中程度
4. 将来の拡張性を確保

**次のステップ**:
1. ユーザーの承認
2. Codeモードでの実装開始
