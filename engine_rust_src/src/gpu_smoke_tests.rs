use crate::core::gpu_manager::GpuManager;
use crate::test_helpers::create_test_db;
use crate::core::gpu_conversions::GpuConverter;

#[test]
fn test_gpu_shader_compiles() {
    let db = create_test_db();
    let (stats, bc) = db.convert_to_gpu();

    // Attempt to initialize the GPU Manager, which compiles the WGSL shaders
    let manager = GpuManager::new(&stats, &bc, wgpu::Backends::all());

    assert!(manager.is_some(), "GPU Manager failed to initialize. The WGSL shader likely contains compile errors.");
}
