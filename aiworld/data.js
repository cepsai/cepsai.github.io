const data = [
  {
    "id": "Mercor (US)",
    "country": "United States",
    "value": 350000000,
    "category": "Software & cloud",
    "x_val": 1,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/mosa7qe2p3jnb81mpmd6"
  },
  {
    "id": "Fireworks AI (US)",
    "country": "United States",
    "value": 230000000,
    "category": "Software & cloud",
    "x_val": 2,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/xgb8cpbz7pcvovoowrmk"
  },
  {
    "id": "Synthesia (GB)",
    "country": "United Kingdom",
    "value": 200000000,
    "category": "Software & cloud",
    "x_val": 3,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/rheqfhayx3jzphoa7bfe"
  },
  {
    "id": "Sublime Security (US)",
    "country": "United States",
    "value": 150000000,
    "category": "Cybersecurity",
    "x_val": 4,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/529740dcc6ea4b1a8543826d0b54c196"
  },
  {
    "id": "Legora (SE)",
    "country": "Sweden",
    "value": 150000000,
    "category": "Legal & Compliance",
    "x_val": 5,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/77870602d6044af49f0dd438ec059977"
  },
  {
    "id": "Harvey (US)",
    "country": "United States",
    "value": 150000000,
    "category": "Legal & Compliance",
    "x_val": 6,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/130c3d3fb2274495adc94f5efde4f7bd"
  },
  {
    "id": "Perfumeo (US)",
    "country": "United States",
    "value": 105450000,
    "category": "Software & cloud",
    "x_val": 7,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/wkvnaultvqwujufdnwa5"
  },
  {
    "id": "Electric Mind (CA)",
    "country": "Canada",
    "value": 100000000,
    "category": "Data",
    "x_val": 8,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/811118dbe32e4557a099b14058c7b780"
  },
  {
    "id": "ConductorOne (US)",
    "country": "United States",
    "value": 79000000,
    "category": "Cybersecurity",
    "x_val": 9,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/tcoxsmcmkl15hmjbl5z0"
  },
  {
    "id": "CoreStory (US)",
    "country": "United States",
    "value": 32000000,
    "category": "Software & cloud",
    "x_val": 10,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/9843eb786f474a38916a00d6a918f5e3"
  },
  {
    "id": "Syllo (US)",
    "country": "United States",
    "value": 30000000,
    "category": "Legal & Compliance",
    "x_val": 11,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/paxlgjd1trtf1w9q2dhf"
  },
  {
    "id": "ISA Saúde (BR)",
    "country": "Brazil",
    "value": 30000000,
    "category": "Health",
    "x_val": 12,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/f46bjfb6mvx2adeyicst"
  },
  {
    "id": "DataLane (US)",
    "country": "United States",
    "value": 25888606,
    "category": "Software & cloud",
    "x_val": 13,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/623c88b2c1984b2685ee95642c246bd1"
  },
  {
    "id": "Mem0 (US)",
    "country": "United States",
    "value": 20000000,
    "category": "Software & cloud",
    "x_val": 14,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/8bc4a5e3e38c4cacb3bbb2fba6132d02"
  },
  {
    "id": "Onfire AI (IL)",
    "country": "Israel",
    "value": 20000000,
    "category": "Data",
    "x_val": 15,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/031e4e48b2da441687b8e1b6018eedb6"
  },
  {
    "id": "Agtonomy (US)",
    "country": "United States",
    "value": 18000000,
    "category": "Industry & Mobility",
    "x_val": 17,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/eh9nzeq58irkphblhd8x"
  },
  {
    "id": "mimic (CH)",
    "country": "Switzerland",
    "value": 16000000,
    "category": "Industry & Mobility",
    "x_val": 18,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/bqhsmb6j9czj1bbpfjgu"
  },
  {
    "id": "Snap Company (KR)",
    "country": "South Korea",
    "value": 14744819,
    "category": "Software & cloud",
    "x_val": 19,
    "logo": 0
  },
  {
    "id": "Null Hypothesis (CN)",
    "country": "China",
    "value": 14087483,
    "category": "Software & cloud",
    "x_val": 20,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/8dace899ba0648578ae0aac6b85ffc1d"
  },
  {
    "id": "Micronano Core (CN)",
    "country": "China",
    "value": 14063906,
    "category": "Industry & Mobility",
    "x_val": 21,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/lxrmfsonjfvhxonpggpb"
  },
  {
    "id": "Impala AI (IL)",
    "country": "Israel",
    "value": 11000000,
    "category": "Software & cloud",
    "x_val": 22,
    "logo": 0
  },
  {
    "id": "Spacial (US)",
    "country": "United States",
    "value": 10000000,
    "category": "Industry & Mobility",
    "x_val": 23,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/a58b6ae189c14aadb28300e1ad501038"
  },
  {
    "id": "Polygraf (US)",
    "country": "United States",
    "value": 9500000,
    "category": "Legal & Compliance",
    "x_val": 24,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/dx1belzo6soghixghr89"
  },
  {
    "id": "Primaa (FR)",
    "country": "France",
    "value": 8141457,
    "category": "Health",
    "x_val": 25,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/9913fadc7cca48c2af55e5b988224af2"
  },
  {
    "id": "Lyzr (US)",
    "country": "United States",
    "value": 8000000,
    "category": "Software & cloud",
    "x_val": 26,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/fotrsjiaxcutudgdvxug"
  },
  {
    "id": "Honey Health (US)",
    "country": "United States",
    "value": 7800000,
    "category": "Health",
    "x_val": 27,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/98ab7a473a8b439fb2cd10c72d87617a"
  },
  {
    "id": "Luminos.AI (US)",
    "country": "United States",
    "value": 7756996,
    "category": "Industry & Mobility",
    "x_val": 28,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/p8r4g778pzcrutk0y1jk"
  },
  {
    "id": "Dazzle AI (US)",
    "country": "United States",
    "value": 7509996,
    "category": "Software & cloud",
    "x_val": 29,
    "logo": 0
  },
  {
    "id": "Wild Moose (US)",
    "country": "United States",
    "value": 7000000,
    "category": "Software & cloud",
    "x_val": 30,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/s2quuzm30eatntokjdbs"
  },
  {
    "id": "Grasp (SE)",
    "country": "Sweden",
    "value": 7000000,
    "category": "Data",
    "x_val": 31,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/rvpezbt3ctnmauhscwci"
  },
  {
    "id": "TestSprite (US)",
    "country": "United States",
    "value": 6700000,
    "category": "Software & cloud",
    "x_val": 32,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/axsqisgngjtko80a09ey"
  },
  {
    "id": "The Prompting Company (US)",
    "country": "United States",
    "value": 6500000,
    "category": "Software & cloud",
    "x_val": 33,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/efe74643c61d486fa89f23d518ea2d65"
  },
  {
    "id": "Human Health (AU)",
    "country": "Australia",
    "value": 5595212,
    "category": "Health",
    "x_val": 34,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/oesxgzsjfzvpslnbflgn"
  },
  {
    "id": "Allie AI (US)",
    "country": "United States",
    "value": 5200000,
    "category": "Industry & Mobility",
    "x_val": 35,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/owgzzo3kct2gpkfwydd2"
  },
  {
    "id": "WorkHero (US)",
    "country": "United States",
    "value": 5000000,
    "category": "Data",
    "x_val": 36,
    "logo": 0
  },
  {
    "id": "The Happy Company (IN)",
    "country": "India",
    "value": 5000000,
    "category": "Cybersecurity",
    "x_val": 37,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/hous67fmcynzf2u0qztt"
  },
  {
    "id": "Adam (US)",
    "country": "United States",
    "value": 4099999,
    "category": "Industry & Mobility",
    "x_val": 38,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/b8d2761a528049a69ca83169ba9c7c68"
  },
  {
    "id": "BigTech Plus (KR)",
    "country": "South Korea",
    "value": 3980281,
    "category": "Finance",
    "x_val": 39,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/dbe8e157d49990aaec7e"
  },
  {
    "id": "Examen (US)",
    "country": "United States",
    "value": 3914591,
    "category": "Software & cloud",
    "x_val": 40,
    "logo": 0
  },
  {
    "id": "RedCarbon (IT)",
    "country": "Italy",
    "value": 3489196,
    "category": "Cybersecurity",
    "x_val": 42,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/pmvgp1ca1gcjqgo5v0gw"
  },
  {
    "id": "Surgical Automations (US)",
    "country": "United States",
    "value": 3400000,
    "category": "Health",
    "x_val": 43,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/vcnoh097qnknacrvq4ap"
  },
  {
    "id": "pieverse (US)",
    "country": "United States",
    "value": 3000000,
    "category": "Software & cloud",
    "x_val": 44,
    "logo": 0
  },
  {
    "id": "Tanbii (US)",
    "country": "United States",
    "value": 3000000,
    "category": "Software & cloud",
    "x_val": 45,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/w5wouiwjandjqlatqmt9"
  },
  {
    "id": "Scavenger AI (DE)",
    "country": "Germany",
    "value": 2902296,
    "category": "Data",
    "x_val": 46,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/ids0j8leu8eofxnfziwt"
  },
  {
    "id": "BITE Data (US)",
    "country": "United States",
    "value": 2500000,
    "category": "Industry & Mobility",
    "x_val": 47,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/e7809d537a9e4841bcfae701c77ae885"
  },
  {
    "id": "Maket (CA)",
    "country": "Canada",
    "value": 2440066,
    "category": "Software & cloud",
    "x_val": 48,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/na5cl1flchfrqtuzrtwc"
  },
  {
    "id": "MEXT (US)",
    "country": "United States",
    "value": 2406992,
    "category": "Software & cloud",
    "x_val": 49,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/5b1d361d3ab94a8389f0d68cc639c525"
  },
  {
    "id": "Flamingo (US)",
    "country": "United States",
    "value": 2200000,
    "category": "Software & cloud",
    "x_val": 50,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/0e0a1de7ff124c52be749babe7b38287"
  },
  {
    "id": "Valkyrie (US)",
    "country": "United States",
    "value": 2000000,
    "category": "Data",
    "x_val": 51,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/eqgrsxltmlvuoe05f7ie"
  },
  {
    "id": "Desktop Commander (LV)",
    "country": "Latvia",
    "value": 1282053,
    "category": "Software & cloud",
    "x_val": 52,
    "logo": 0
  },
  {
    "id": "Solatis (US)",
    "country": "United States",
    "value": 1200000,
    "category": "Software & cloud",
    "x_val": 53,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/6af3227dafaf448881bbe52f08581b70"
  },
  {
    "id": "DoctorNow (US)",
    "country": "United States",
    "value": 1008055,
    "category": "Software & cloud",
    "x_val": 54,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/me5q1igt7gukvf0pb8un"
  },
  {
    "id": "Art Recognition (CH)",
    "country": "Switzerland",
    "value": 1000000,
    "category": "Software & cloud",
    "x_val": 55,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/ekh9xoofp0mrh4beeqlc"
  },
  {
    "id": "Legal Mind (NL)",
    "country": "The Netherlands",
    "value": 874127,
    "category": "Legal & Compliance",
    "x_val": 56,
    "logo": 0
  },
  {
    "id": "twiggy (BR)",
    "country": "Brazil",
    "value": 653058,
    "category": "Software & cloud",
    "x_val": 57,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/scb8trnt32nbh9zlu7j0"
  },
  {
    "id": "Ultrassure (CA)",
    "country": "Canada",
    "value": 333000,
    "category": "Finance",
    "x_val": 58,
    "logo": 0
  },
  {
    "id": "Bixie Technologies (ZA)",
    "country": "South Africa",
    "value": 300000,
    "category": "Health",
    "x_val": 59,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/b04fc1fb738d48a2a3d67ea32ebe22b7"
  },
  {
    "id": "Cloud Cycle (GB)",
    "country": "United Kingdom",
    "value": 141211,
    "category": "Software & cloud",
    "x_val": 60,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/fdv5szfxkfdtncu2filw"
  },
  {
    "id": "Rmz.ai (SA)",
    "country": "Saudi Arabia",
    "value": 100000,
    "category": "Software & cloud",
    "x_val": 61,
    "logo": 0
  },
  {
    "id": "Agiloop (US)",
    "country": "United States",
    "value": 85000,
    "category": "Software & cloud",
    "x_val": 62,
    "logo": 0
  },
  {
    "id": "Menta (AR)",
    "country": "Argentina",
    "value": 50000,
    "category": "Health",
    "x_val": 63,
    "logo": 0
  },
  {
    "id": "Rivellium (PL)",
    "country": "Poland",
    "value": 50000,
    "category": "Finance",
    "x_val": 64,
    "logo": 0
  },
  {
    "id": "Storytailor (US)",
    "country": "United States",
    "value": 22000,
    "category": "Software & cloud",
    "x_val": 65,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/mhy4rmpbcfekjvtwvlxp"
  },
  {
    "id": "Elerian AI (GB)",
    "country": "United Kingdom",
    "value": 15339,
    "category": "Software & cloud",
    "x_val": 66,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/gexwihwm39iert4iqakz"
  },
  {
    "id": "Mifu (GB)",
    "country": "United Kingdom",
    "value": 13338,
    "category": "Software & cloud",
    "x_val": 67,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/eac3a17f86914c518d5e164c25a45299"
  },
  {
    "id": "Noxi (US)",
    "country": "United States",
    "value": 6000,
    "category": "Software & cloud",
    "x_val": 68,
    "logo": "https://images.crunchbase.com/image/upload/t_cb-default-original/5e769427114a4a3991105c19a9be4365"
  }
];