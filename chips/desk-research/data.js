// Training-hardware desk research (CEPS AI World, 2026)
// Sources: public statements, press reports. Status reflects evidence level.
window.DATA = {
  companies: [
    { id: "deepseek",   name: "DeepSeek",            label: "DeepSeek",          country: "CN" },
    { id: "moonshot",   name: "Moonshot (Kimi K2)",  label: "Moonshot",          country: "CN" },
    { id: "alibaba",    name: "Alibaba (Qwen)",      label: "Alibaba",           country: "CN" },
    { id: "tencent",    name: "Tencent (Hunyuan)",   label: "Tencent",           country: "CN" },
    { id: "baidu",      name: "Baidu (Qianfan/Ernie)", label: "Baidu",           country: "CN" },
    { id: "minimax",    name: "MiniMax",             label: "MiniMax",           country: "CN" },
    { id: "xiaomi",     name: "Xiaomi (MiMo)",       label: "Xiaomi",            country: "CN" },
    { id: "zhipu",      name: "Zhipu (GLM-5)",       label: "Zhipu",             country: "CN" },
    { id: "nvidia-lab", name: "NVIDIA (Nemotron)",   label: "NVIDIA Research",   country: "US" },
    { id: "google",     name: "Google (Gemma)",      label: "Google",            country: "US" },
    { id: "microsoft",  name: "Microsoft (Phi)",     label: "Microsoft",         country: "US" },
    { id: "meta",       name: "Meta (Llama)",        label: "Meta",              country: "US" },
    { id: "poolside",   name: "Poolside (Laguna)",   label: "Poolside",          country: "US" }
  ],
  hardware: [
    { id: "nvidia",         name: "NVIDIA (H100 / H800 / Blackwell)", label: "NVIDIA",            country: "US", kind: "merchant" },
    { id: "huawei",         name: "Huawei Ascend",                    label: "Huawei Ascend",     country: "CN", kind: "merchant" },
    { id: "google-tpu",     name: "Google TPU (v4p / v5p / v5e)",     label: "Google TPU",        country: "US", kind: "in-house" },
    { id: "alibaba-thead",  name: "Alibaba T-Head / Pingtouge",       label: "Alibaba T-Head",    country: "CN", kind: "in-house" },
    { id: "baidu-kunlun",   name: "Baidu Kunlun P800",                label: "Baidu Kunlun",      country: "CN", kind: "in-house" },
    { id: "chinese-misc",   name: "Chinese chips (unspecified)",      label: "Chinese chips",     country: "CN", kind: "merchant" },
    { id: "undisclosed",    name: "Undisclosed",                      label: "Undisclosed",       country: "?",  kind: "?" }
  ],
  // status: confirmed | alleged | rumored | historical | undisclosed
  links: [
    { source: "deepseek",   target: "huawei",        status: "confirmed",   note: "V4 trained on Huawei Ascend" },
    { source: "deepseek",   target: "nvidia",        status: "confirmed",   note: "V3 trained on H800s" },
    { source: "moonshot",   target: "nvidia",        status: "confirmed",   note: "Kimi K2 on H800" },
    { source: "alibaba",    target: "nvidia",        status: "alleged",     note: "Allegedly trains on NVIDIA" },
    { source: "alibaba",    target: "alibaba-thead", status: "alleged",     note: "Reportedly uses in-house T-Head silicon in some runs" },
    { source: "tencent",    target: "huawei",        status: "alleged",     note: "Pivoted from NVIDIA; allegedly Huawei Ascend for training" },
    { source: "tencent",    target: "nvidia",        status: "historical",  note: "Pre-pivot training" },
    { source: "baidu",      target: "baidu-kunlun",  status: "confirmed",   note: "Qianfan on Kunlun P800" },
    { source: "baidu",      target: "undisclosed",   status: "undisclosed", note: "Ernie training stack undisclosed" },
    { source: "minimax",    target: "nvidia",        status: "confirmed",   note: "M1 / Text-01 on H800" },
    { source: "minimax",    target: "chinese-misc",  status: "rumored",     note: "M2.7 rumored on Chinese chips" },
    { source: "xiaomi",     target: "undisclosed",   status: "undisclosed", note: "MiMo training stack undisclosed" },
    { source: "zhipu",      target: "huawei",        status: "confirmed",   note: "GLM-5 on Huawei Ascend" },
    { source: "nvidia-lab", target: "nvidia",        status: "confirmed",   note: "H100 + Blackwell + NVFP4" },
    { source: "google",     target: "google-tpu",    status: "confirmed",   note: "v4p / v5p / v5e" },
    { source: "microsoft",  target: "nvidia",        status: "confirmed",   note: "Phi on H100 / A100" },
    { source: "meta",       target: "nvidia",        status: "confirmed",   note: "Llama on NVIDIA chips" },
    { source: "poolside",   target: "nvidia",        status: "confirmed",   note: "Pure NVIDIA training stack" }
  ]
};
