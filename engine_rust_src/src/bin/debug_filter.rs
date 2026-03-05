use engine_rust::core::logic::filter::CardFilter;

fn main() {
    let attr_val: i64 = 36028797104226305;
    let filter = CardFilter::from_attr(attr_val);
    println!("Unpacked Filter: {:#?}", filter);
}
