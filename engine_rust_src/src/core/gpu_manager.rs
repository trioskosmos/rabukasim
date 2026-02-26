use std::sync::Mutex;
use wgpu::util::DeviceExt;
use pollster::block_on;
use crate::core::gpu_state::{GpuGameState, GpuCardStats};

pub const MAX_BATCH_SIZE: usize = 65_000; // Fits within 128MB limit with 1936-byte GpuGameState

pub struct GpuManager {
    pub device: wgpu::Device,
    pub queue: wgpu::Queue,
    pub compute_pipeline: wgpu::ComputePipeline,
    pub card_stats_buffer: wgpu::Buffer,
    pub bytecode_buffer: wgpu::Buffer,
    pub state_buffer: wgpu::Buffer,
    pub readback_buffer: wgpu::Buffer,
    pub score_buffer: wgpu::Buffer,
    pub score_readback_buffer: wgpu::Buffer,
    pub bind_group: wgpu::BindGroup,
    pub lock: Mutex<()>,
}

impl GpuManager {
    pub fn new(card_data: &[GpuCardStats], bytecode_data: &[i32], backends: wgpu::Backends) -> Option<Self> {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor {
            backends,
            ..Default::default()
        });
        let adapter = block_on(instance.request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance,
            ..Default::default()
        }))?;
        let info = adapter.get_info();
        let limits = adapter.limits();
        println!("Selected Adapter: {:?} (Backend: {:?}, Max Binding Size: {} MB)", info.name, info.backend, limits.max_storage_buffer_binding_size / 1024 / 1024);
        std::io::Write::flush(&mut std::io::stdout()).unwrap();

        println!("DEBUG: Requesting device...");
        std::io::Write::flush(&mut std::io::stdout()).unwrap();
        let (device, queue) = block_on(adapter.request_device(
            &wgpu::DeviceDescriptor {
                label: Some("MCTS Compute Device"),
                required_features: wgpu::Features::empty(),
                required_limits: wgpu::Limits::default().using_resolution(adapter.limits()),
                memory_hints: wgpu::MemoryHints::default(),
            },
            None,
        )).ok()?;

        println!("DEBUG: Creating shader module...");
        std::io::Write::flush(&mut std::io::stdout()).unwrap();
        let shader_src: &'static str = concat!(
                    include_str!("shader_types.wgsl"), "\n",
                    include_str!("shader_helpers.wgsl"), "\n",
                    include_str!("shader_rules.wgsl"), "\n",
                    include_str!("shader_heuristic_pure.wgsl"), "\n",
                    include_str!("shader_main.wgsl")
                );

        // PERSIST FOR EXTERNAL AUDIT (per user recommendation)
        let _ = std::fs::write("debug_concatenated_shader.wgsl", shader_src);

        // Naga's recursive WGSL compiler needs more than the default 1MB Windows stack.
        // The calling binary must ensure sufficient stack size (see test_gpu_parity.rs).
        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("MCTS Shader"),
            source: wgpu::ShaderSource::Wgsl(shader_src.into()),
        });

        println!("DEBUG: Creating pipeline layout...");
        std::io::Write::flush(&mut std::io::stdout()).unwrap();

        let bind_group_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("MCTS Bind Group Layout"),
            entries: &[
                wgpu::BindGroupLayoutEntry {
                    binding: 0,
                    visibility: wgpu::ShaderStages::COMPUTE,
                    ty: wgpu::BindingType::Buffer {
                        ty: wgpu::BufferBindingType::Storage { read_only: false },
                        has_dynamic_offset: false,
                        min_binding_size: None,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 1,
                    visibility: wgpu::ShaderStages::COMPUTE,
                    ty: wgpu::BindingType::Buffer {
                        ty: wgpu::BufferBindingType::Storage { read_only: true },
                        has_dynamic_offset: false,
                        min_binding_size: None,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 2,
                    visibility: wgpu::ShaderStages::COMPUTE,
                    ty: wgpu::BindingType::Buffer {
                        ty: wgpu::BufferBindingType::Storage { read_only: true },
                        has_dynamic_offset: false,
                        min_binding_size: None,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 3,
                    visibility: wgpu::ShaderStages::COMPUTE,
                    ty: wgpu::BindingType::Buffer {
                        ty: wgpu::BufferBindingType::Storage { read_only: false },
                        has_dynamic_offset: false,
                        min_binding_size: None,
                    },
                    count: None,
                },
            ],
        });

        let pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("MCTS Pipeline Layout"),
            bind_group_layouts: &[&bind_group_layout],
            push_constant_ranges: &[],
        });

        println!("DEBUG: Creating compute pipeline...");
        std::io::Write::flush(&mut std::io::stdout()).unwrap();
        let compute_pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
            label: Some("MCTS Pipeline"),
            layout: Some(&pipeline_layout),
            module: &shader,
            entry_point: "main",
            compilation_options: wgpu::PipelineCompilationOptions::default(),
            cache: None,
        });

        println!("DEBUG: Creating buffers...");
        std::io::Write::flush(&mut std::io::stdout()).unwrap();
        let card_stats_buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("Card Stats Buffer"),
            contents: bytemuck::cast_slice(card_data),
            usage: wgpu::BufferUsages::STORAGE,
        });

        let bytecode_buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: Some("Bytecode Buffer"),
            contents: bytemuck::cast_slice(bytecode_data),
            usage: wgpu::BufferUsages::STORAGE,
        });

        println!("DEBUG: Allocated static buffers.");
        std::io::Write::flush(&mut std::io::stdout()).unwrap();

        // Pre-allocate simulation buffers
        let state_buffer_size = (MAX_BATCH_SIZE * std::mem::size_of::<GpuGameState>()) as u64;
        println!("DEBUG: Allocating state buffer (Size: {} bytes, MAX_BATCH: {})...", state_buffer_size, MAX_BATCH_SIZE);
        std::io::Write::flush(&mut std::io::stdout()).unwrap();
        let state_buffer = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("Pre-allocated State Buffer"),
            size: state_buffer_size,
            usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });

        println!("DEBUG: Allocating readback buffer...");
        std::io::Write::flush(&mut std::io::stdout()).unwrap();
        let readback_buffer = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("Pre-allocated Readback Buffer"),
            size: state_buffer_size,
            usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });

        println!("DEBUG: Allocated simulation buffers.");
        std::io::Write::flush(&mut std::io::stdout()).unwrap();

        let score_buffer_size = (MAX_BATCH_SIZE * 4) as u64;
        let score_buffer = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("Score Buffer"),
            size: score_buffer_size,
            usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
            mapped_at_creation: false,
        });
        let score_readback_buffer = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("Score Readback Buffer"),
            size: score_buffer_size,
            usage: wgpu::BufferUsages::MAP_READ | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });

        // Persistent Bind Group
        let bind_group = device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("Compute Bind Group"),
            layout: &bind_group_layout,
            entries: &[
                wgpu::BindGroupEntry {
                    binding: 0,
                    resource: state_buffer.as_entire_binding(),
                },
                wgpu::BindGroupEntry {
                    binding: 1,
                    resource: card_stats_buffer.as_entire_binding(),
                },
                wgpu::BindGroupEntry {
                    binding: 2,
                    resource: bytecode_buffer.as_entire_binding(),
                },
                wgpu::BindGroupEntry {
                    binding: 3,
                    resource: score_buffer.as_entire_binding(),
                },
            ],
        });

        Some(Self {
            device,
            queue,
            compute_pipeline,
            card_stats_buffer,
            bytecode_buffer,
            state_buffer,
            readback_buffer,
            score_buffer,
            score_readback_buffer,
            bind_group,
            lock: Mutex::new(()),
        })
    }

    pub fn run_simulations_into(&self, input_states: &[GpuGameState], output_states: &mut [GpuGameState]) {
        if input_states.is_empty() { return; }

        let _guard = self.lock.lock().unwrap();

        let count = input_states.len();
        if count > MAX_BATCH_SIZE {
            panic!("Batch size {} exceeds pre-allocated limit {}", count, MAX_BATCH_SIZE);
        }
        if output_states.len() < count {
            panic!("Output slice too small for result count {}", count);
        }

        let state_buffer_size = (count * std::mem::size_of::<GpuGameState>()) as u64;

        // Efficiently upload data to the pre-allocated GPU buffer
        self.queue.write_buffer(&self.state_buffer, 0, bytemuck::cast_slice(input_states));

        let mut encoder = self.device.create_command_encoder(&wgpu::CommandEncoderDescriptor {
            label: Some("Compute Encoder"),
        });

        {
            let mut compute_pass = encoder.begin_compute_pass(&wgpu::ComputePassDescriptor {
                label: Some("Compute Pass"),
                timestamp_writes: None,
            });
            compute_pass.set_pipeline(&self.compute_pipeline);
            compute_pass.set_bind_group(0, &self.bind_group, &[]);
            // ITERATIVE DISPATCH: 200 steps to cover typical game length
            for _ in 0..200 {
                compute_pass.dispatch_workgroups(((count + 63) / 64) as u32, 1, 1);
            }
        }

        // Copy result to the readback buffer for mapping
        encoder.copy_buffer_to_buffer(&self.state_buffer, 0, &self.readback_buffer, 0, state_buffer_size);

        self.queue.submit(Some(encoder.finish()));

        let buffer_slice = self.readback_buffer.slice(..state_buffer_size);
        let (sender, receiver) = std::sync::mpsc::channel();
        buffer_slice.map_async(wgpu::MapMode::Read, move |v| sender.send(v).unwrap());

        self.device.poll(wgpu::Maintain::Wait);

        if let Ok(Ok(())) = receiver.recv() {
            let data = buffer_slice.get_mapped_range();
            let result_slice: &[GpuGameState] = bytemuck::cast_slice(&data);
            output_states[..count].copy_from_slice(result_slice);
            drop(data);
            self.readback_buffer.unmap();
        } else {
            panic!("Failed to map GPU buffer");
        }
    }

    /// Run a single GPU step for parity testing.
    /// Unlike run_simulations_into (which runs 200 steps for MCTS),
    /// this executes exactly one shader dispatch for precise state comparison.
    pub fn run_single_step(&self, input_states: &[GpuGameState], output_states: &mut [GpuGameState]) {
        self.run_multi_step(input_states, output_states, 1);
    }

    /// Run multiple GPU steps for parity testing.
    /// This is needed for cards that require interaction resolution (LOOK_AND_CHOOSE, etc.)
    /// Each step executes one shader dispatch, which may advance the game state.
    pub fn run_multi_step(&self, input_states: &[GpuGameState], output_states: &mut [GpuGameState], steps: usize) {
        if input_states.is_empty() { return; }

        let _guard = self.lock.lock().unwrap();

        let count = input_states.len();
        if count > MAX_BATCH_SIZE {
            panic!("Batch size {} exceeds pre-allocated limit {}", count, MAX_BATCH_SIZE);
        }
        if output_states.len() < count {
            panic!("Output slice too small for result count {}", count);
        }

        let state_buffer_size = (count * std::mem::size_of::<GpuGameState>()) as u64;

        // Upload data to GPU
        self.queue.write_buffer(&self.state_buffer, 0, bytemuck::cast_slice(input_states));

        let mut encoder = self.device.create_command_encoder(&wgpu::CommandEncoderDescriptor {
            label: Some("Multi Step Compute Encoder"),
        });

        {
            let mut compute_pass = encoder.begin_compute_pass(&wgpu::ComputePassDescriptor {
                label: Some("Multi Step Compute Pass"),
                timestamp_writes: None,
            });
            compute_pass.set_pipeline(&self.compute_pipeline);
            compute_pass.set_bind_group(0, &self.bind_group, &[]);
            // MULTI DISPATCH: Execute multiple steps for interaction resolution
            for _ in 0..steps {
                compute_pass.dispatch_workgroups(((count + 63) / 64) as u32, 1, 1);
            }
        }

        // Copy result to readback buffer
        encoder.copy_buffer_to_buffer(&self.state_buffer, 0, &self.readback_buffer, 0, state_buffer_size);

        self.queue.submit(Some(encoder.finish()));

        // Read back results
        let buffer_slice = self.readback_buffer.slice(..state_buffer_size);
        let (sender, receiver) = std::sync::mpsc::channel();
        buffer_slice.map_async(wgpu::MapMode::Read, move |v| sender.send(v).unwrap());

        self.device.poll(wgpu::Maintain::Wait);

        if let Ok(Ok(())) = receiver.recv() {
            let data = buffer_slice.get_mapped_range();
            let result_slice: &[GpuGameState] = bytemuck::cast_slice(&data);
            output_states[..count].copy_from_slice(result_slice);
            drop(data);
            self.readback_buffer.unmap();
        } else {
            panic!("Failed to map GPU buffer");
        }
    }

    /// Process large batches in smaller chunks for better GPU scheduling
    /// and reduced peak VRAM usage. Optimal chunk size is typically 50k-100k.
    pub fn run_simulations_chunked(
        &self,
        input_states: &[GpuGameState],
        output_states: &mut [GpuGameState],
        chunk_size: usize,
    ) {
        let total = input_states.len();
        if total == 0 { return; }
        if output_states.len() < total {
            panic!("Output slice too small");
        }
        let chunk_size = chunk_size.min(MAX_BATCH_SIZE);

        for start in (0..total).step_by(chunk_size) {
            let end = (start + chunk_size).min(total);
            self.run_simulations_into(
                &input_states[start..end],
                &mut output_states[start..end],
            );
        }
    }
    pub fn run_simulations_scores(&self, input_states: &[GpuGameState], output_scores: &mut [f32]) {
        if input_states.is_empty() { return; }
        let _guard = self.lock.lock().unwrap();
        let count = input_states.len();
        if count > MAX_BATCH_SIZE { panic!("Batch size too large"); }
        if output_scores.len() < count { panic!("Target buffer too small"); }

        self.queue.write_buffer(&self.state_buffer, 0, bytemuck::cast_slice(input_states));
        let mut encoder = self.device.create_command_encoder(&wgpu::CommandEncoderDescriptor { label: None });
        {
            let mut compute_pass = encoder.begin_compute_pass(&wgpu::ComputePassDescriptor { label: None, timestamp_writes: None });
            compute_pass.set_pipeline(&self.compute_pipeline);
            compute_pass.set_bind_group(0, &self.bind_group, &[]);
            for _ in 0..200 {
                compute_pass.dispatch_workgroups(((count + 63) / 64) as u32, 1, 1);
            }
        }
        encoder.copy_buffer_to_buffer(&self.score_buffer, 0, &self.score_readback_buffer, 0, (count * 4) as u64);
        self.queue.submit(Some(encoder.finish()));

        let slice = self.score_readback_buffer.slice(..(count * 4) as u64);
        let (tx, rx) = std::sync::mpsc::channel();
        slice.map_async(wgpu::MapMode::Read, move |v| tx.send(v).unwrap());
        self.device.poll(wgpu::Maintain::Wait);
        if let Ok(Ok(())) = rx.recv() {
            let data = slice.get_mapped_range();
            output_scores[..count].copy_from_slice(bytemuck::cast_slice(&data));
            drop(data);
            self.score_readback_buffer.unmap();
        }
    }
}
