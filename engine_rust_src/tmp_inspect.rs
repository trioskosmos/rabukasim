use engine_rust::test_helpers::load_real_db;
fn main(){
 let db = load_real_db();
 let cid = 4684;
 let m = db.get_member(cid).unwrap();
 let ab = &m.abilities[0];
 println!("ability effects len={} frames={} choice_flags={} v? modal_count={}", ab.effects.len(), ab.frames().len(), ab.choice_flags, ab.modal_option_count());
 for (i,f) in ab.frames().iter().enumerate(){
   println!("frame {} op={} val={} attr={} slot={} {:?}", i, f.opcode(), f.value(), f.attr(), f.slot(), f);
 }
 for idx in 0..ab.modal_option_count(){
   println!("option {}:", idx);
   if let Some(frames)=ab.get_modal_option_frames(idx as usize){
     for (j,f) in frames.iter().enumerate(){
       println!("  [{}] op={} val={} attr={} slot={} {:?}", j, f.opcode(), f.value(), f.attr(), f.slot(), f);
     }
   } else {
     println!("  none");
   }
 }
}
