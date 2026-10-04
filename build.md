## CI

GitHub Actions (`.github/workflows/build.yml`)

每次 push 到 `main`、每个 PR、以及手动 `workflow_dispatch` 都会在 **windows-latest** 上走一遍
「`merge.py` → spcomp → 校验 → 上传 artifact」,从 Actions 运行页面下载。**不自动提交回仓库、也不发 Release**。

**artifact 是部署形状的** —— 解压后的目录结构与 `%SRV%\bms\` 同形,把它解压/覆盖到服务器根目录即可:

```
BMAG-<sha>.zip
├── bms/addons/sourcemod/plugins/BMAG.smx   ← 解压到 %SRV%\ 后自动落到正确位置
└── build.log                               ← 编译日志,排查用
```

> **artifact 是完整部署包**:它把仓库的 `bms/` 整个复制进去,再把这次编出的 `BMAG.smx`
> 放进 `bms/addons/sourcemod/plugins/`。所以**解压到 `%SRV%\` 就是一次完整部署**,
> 不需要再单独拷 `bms/`(这正是仓库里不含 `BMAG.smx` 的补偿 —— 见[部署](#部署)方式 A)。

用 windows runner 是有意的:仓库里固化的工具链 `smx_analysis/dl/.../spcomp.exe`
(SourcePawn 1.12.0.7255)是 Windows 可执行文件,原生跑即可,不需要 wine;用它而不是现下载编译器,
是为了让它与同样入库的 `include/` 严格对应。

CI 的门禁由 `smx_analysis/ci_check.py` 提供,查三件编译器看不见的事:

| 检查 | 为什么 |
|---|---|
| 合并出的模块集 == 16 个预期模块 | BMAG 的设计前提是**不含任何官方插件**;万一有人把官方模块并回去,命令会与官方 `.smx` 重复注册 —— 那**只在服务器加载时才炸**,编译期完全看不出来 |
| 不出现 `mod_adminmenu_` / `mod_basecomm_` / `mod_clientprefs_` / `mod_mapchooser_` / `mod_adminhelp_` | 这些是 `merge.py` 给同插件内模块加的符号前缀;出现即表示某个模块被移出 `MODULES` 但调用方没同步处理 |
| 警告数 == 基线(26),且日志的汇总行与逐条明细自洽 | 警告数漂移往往意味着模块被误加/误删;汇总与明细一致则能挡住日志被截断 |

> 警告基线同时写在这里和 workflow 的 `WARN_BASELINE` 环境变量里 —— **有意改动导致警告数变化时,两处一起改**。
> 另外 `ci_check.py` 会在读不出 `N Warnings.` 汇总时**直接判失败**而不是当成 0 警告,避免门禁被静默架空。

> CI **不做哈希比对**:spcomp 不可字节复现(实测见下),每次编出的字节都不一样,拿哈希当门禁只会永远失败。
> 也正因为成品不入库,CI artifact 是**唯一现成的 `BMAG.smx` 来源**(另一个是自己构建)。

> `src/scripting/compile_all.sh` 是构建者留下的"逐个编译 `plugins/*.sp`"批处理脚本,
> 里面的 `SPCOMP` 路径硬编码成 `/c/tmp/smx_analysis/...`,**在本仓库里并不存在**,
> 直接跑会全部失败 —— 要批量编单个插件,把那一行改成 `smx_analysis/dl/...` 的真实路径即可。
> 合并构建走上面的 `merge.py`,不依赖这个脚本。

`merge.py` 只桥接**精确的** SourceMod forward 名,`bms_match` 用自己的 `Bms_` 前缀实现生命周期回调,
靠 `FORWARD_ALIASES` 映射回标准名 —— 改动 forward 命名时务必同步该表,否则回调会静默失效。

**注意事项**:

- spcomp 输出**不是字节可复现的** —— 实测:输入 `BMAG.sp` 内容哈希恒定、mtime 固定、输出路径固定,连编 12 次得到 **4 种不同产物**(两个主变体各出现 5 次,另两个各 1 次,大小在 99168–99170 之间摆动)。原因是编译期内部哈希表序受 ASLR 影响。所以判断新旧请以功能验证或日志为准,**不要比对 MD5 / 文件大小**
- 编译用的 `include/` 必须与生产服务器一致:旧版 `sourcemod.inc` 的 `StoreToAddress` 只有 3 个参数,会编译报错
- **签名必须抗重定位** —— `GameConfGetAddress` 扫的是已加载内存,含绝对地址(`imm32`)的签名会因 base relocation 在运行时失配(磁盘命中、内存不命中,静默不生效)。用 `smx_analysis/sig_check.py` 校验(**结论出自已移出本仓库的 `tau_mp` 的签名**)
- 本仓库现在的构建只涉及 `src/scripting/plugins/` 下的模块 + `include/`;`merge.py` 与上面的编译命令都不涉及任何外部项目


## 从源码构建

```bash
cd smx_analysis
python merge.py          # 生成 src/scripting/BMAG/BMAG.sp(16 模块合并)
```

然后用 spcomp 编译(编译器随仓库放在 `dl/` 下):

```bash
./dl/spcomp.exe \
  -i "src/scripting/include" \
  -o "src/scripting/BMAG/BMAG.smx" \
  "src/scripting/BMAG/BMAG.sp"
```

基线:**26 个警告、0 个错误**(升到 SourceMod 1.12 之前是 35;第二批清理把官方插件移出前是 48,
删掉 SourceBans++ 之前是 50)。
这套命令已于 2026-10-04 在本仓库用 **1.12.0.7255** 复跑验证过,警告数与上述基线一致。