"""Archive earlier sale and mint announcements recovered in final timeline review."""
from collect_stage4 import run
run([
 ('july_2026_arc_8k','https://www.sec.gov/Archives/edgar/data/1876042/000187604226000205/crcl-20260629.htm'),
 ('july_2026_arc_8k_index','https://www.sec.gov/Archives/edgar/data/1876042/000187604226000205/0001876042-26-000205-index.htm'),
 ('arc_launch_ir_release','https://investor.circle.com/news/news-details/2026/Circle-Launches-Arc-Mainnet-an-Economic-Operating-System-for-the-Internet/'),
 ('arc_blog_index_final','https://www.arc.io/blog'),
])
