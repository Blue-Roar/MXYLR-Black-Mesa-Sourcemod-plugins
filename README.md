# BMAG 黑山比赛服整合插件

Black Mesa (黑山起源)的 SourceMod **比赛服整合插件**

是[上游仓库](https://github.com/MXYLR/MXYLR-Black-Mesa-Sourcemod-plugins)的修改版。

> **单人战役的 `tau_mp` / `hl1tau` 插件已从本仓库移除**，如有需要请查看上游仓库

> **想直接开服** → **最快是拿 CI 的完整包**:Actions 里下 `BMAG-<sha>.zip`,解压到 `%SRV%\` 就完事
> (包里 = 仓库 `bms/` + 新编的 `BMAG.smx`)。自己构建也行,见[部署](#部署)。
> 两者都要先过一遍 [⚠️ 部署前必改清单](#️-部署前必改清单):配置里还带着原服的服务器名、群号、域名。
> **想改插件** → [构建#从源码构建](build.md#从源码构建),`merge.py` 把 16 个模块合并成一个 `BMAG.sp` 再交给 spcomp 编译。
> **只想抄某个功能** → [一、`bms_match`](#一bms_match--比赛插件自研) 是自研比赛插件,[二、其它自研模块](#二其它自研--深度改造模块) 列了 9 个深度改造模块。

---

## ⚠️ 部署前必改清单

本仓库是从一台**已经在跑的**服务器上整理出来的，配置里仍带着原服的服务器名、
群号、域名、账号和**占位 SteamID**。直接照抄开服，你的服务器会顶着别人的名字、
把玩家引到别人的群和网站，而你本人拿不到任何管理员权限。

下表是全部需要动手的地方;每个文件的顶部也都写了同样的提示,
搜 `>>>` 就能在文件里定位到具体那一行。

| 文件 | 改什么 | 怎么改 |
|---|---|---|
| `bms/cfg/server.cfg` | `hostname`、`rcon_password`、`sv_region`、`tv_title`/`tv_name`、`maxplayers`、`sv_password` | 改成你自己服务器的信息 |
| `bms/cfg/server.cfg` | `sv_downloadurl`、`sm_motd_url` | 换成你的域名;**没有 FastDL 就把 `sv_downloadurl` 整行注释掉**(玩家回退 srcds 直传,慢但能连)。`sm_motd_url` 需由插件创建才生效 —— 见[已知问题](#已知问题) |
| `bms/cfg/server.cfg` | `is_weaponfix_saddr` | 填**外网玩家能连到的**公网 `IP:端口`,不能留 `127.0.0.1`,否则武器动画修复静默失效 |
| `bms/cfg/server.cfg` | `sm_bms_webpanel_url` | 详见[网页面板走反代部署](webpanel.md) |
| `bms/addons/sourcemod/configs/advertisements.txt` | 两条 `chat` 文案 | 原服的群号和 B 站账号,换成你的 |
| `bms/addons/sourcemod/configs/bms_match.cfg` | `SourceTV` → `DownloadBase` | 改成你的地址,或留空 `""`(录像仍会录,只是下载链接不可用) |
| `bms/cfg/mapcycle_ffa.txt`、`bms/cfg/mapcycle_tdm.txt` | 地图名单 | 删掉你服务器上**没有**的地图,否则换图失败 |

**本仓库不再附带 SourceMod 自身的配置文件** —— 管理员名单、`core.cfg`、`admin_levels/groups/overrides`、
`maplists.cfg`、`geoip/`、`sql-init-scripts/`、`adminmenu_*.txt` 等都属于 SourceMod 官方安装的一部分,
**由你自己的 SourceMod 提供**(与[官方插件交给用户自己装](#三官方插件全部交给用户自己装)是同一条原则)。
所以下面这两件事要在**你的** SourceMod 安装里做:

| 在哪里 | 做什么 |
|---|---|
| `<你的 SourceMod>/configs/admins.cfg` | 填真实 SteamID(原服那份是占位值 `STEAM_0:x:1000000xx`),否则你没有任何管理员权限。读它的是官方插件 `admin-flatfile.smx`(默认启用) |
| `<你的 SourceMod>/configs/databases.cfg` | 只有用 `clientprefs` 持久化 cookie、或是使用 SourceBans 等依赖数据库的插件时才需要建(里面是数据库密码,本仓库故意不含) |

**不需要改**(照抄即可):`bms/cfg/autoexec.cfg`、`bms/cfg/listenserver.cfg`、
`bms/addons/sourcemod/configs/downloads.ini` 等。

**辅助脚本里的路径也是硬编码的**,换机器要改(不改不影响开服,只影响你跑这些脚本):

| 文件 | 硬编码内容 |
|---|---|
| `smx_analysis/watch_launch.ps1` | `F:\BMServer\srcds.exe`、`F:\BMServer\bms\console.log` |
| `smx_analysis/src/scripting/compile_all.sh` | `SPCOMP="/c/tmp/smx_analysis/dl/..."`(该路径在本仓库里**并不存在**,见 [构建#从源码构建](build.md#从源码构建)) |

> `core.cfg` 的 `ServerLang` 保持 SourceMod 默认的 `"en"` 即可,不用改 ——
> 各插件 `translations/*.phrases.txt` 的语言键写法不统一(`schinese` / `zh` / `en` 混用),
> `en` 是三份都有的一份,也是兜底档。

---

## 目录结构

**可部署内容全部集中在一棵树里**:`bms/` 与服务器上的 `%SRV%\bms\` **同形**,
部署就是把它整个覆盖过去(见[部署](#部署))。其余顶层目录都不上服务器。

```
├── bms/                          ★ 部署覆盖树 —— 直接覆盖到 %SRV%\bms\
│   ├── addons/sourcemod/
│   │   ├── plugins/
│   │   │   ├── BMAG.smx               ★ 16 模块合一插件 —— **不入库**,构建/CI 产出后放这里
│   │   │   ├── bms_rpgReloadFix.smx   第三方:RPG 换弹修复
│   │   │   ├── bms_weapon_tauStuckFix.smx 第三方:tau 低弹药卡枪修复
│   │   │   ├── is_weaponfx.smx        第三方:武器动画预热
│   │   │   ├── is_bms_fix_timelimit.smx 第三方:回合时限/倒计时修复
│   │   │   └── disabled/              停用插件(spawn_marker 共 1 个)
│   │   ├── translations/          各插件短语文件(**运行时读取,不编进 BMAG.smx**)
│   │   ├── configs/               **只放本项目自己的配置**:bms_match.cfg、
│   │   │                          bms_webpanel.html、advertisements.txt、downloads*.ini
│   │   └── extensions/socket.ext.dll  BMAG 硬依赖的 socket 扩展(见部署一节)
│   └── cfg/                       服务器 cfg(server.cfg、autoexec、listenserver、
│                                  mapcycle_ffa/tdm.txt、server_match.cfg、
│                                  server_match_post.cfg)
├── smx_analysis/                 构建流水线与源码(**不上服务器**)
│   ├── merge.py                  把 16 个模块源码合并成 BMAG.sp(唯一的构建入口)
│   ├── ci_check.py               CI 门禁:模块集 / 残留符号 / 警告基线
│   ├── fix_merge.py              merge.py 的补丁工具
│   ├── sig_check.py              签名抗重定位校验(见"从源码构建")
│   ├── rcon.py                   RCON 调试客户端(凭据走环境变量)
│   ├── bisect_compile.py         二分定位编译失败的模块
│   ├── bctest.sp                 最小插件骨架,用于冒烟验证编译/加载链路
│   ├── mvf.html / mvf_wb.html    missing_viewmodel_fix 的参考来源抓取
│   │                             (mvf_wb.html 是 AlliedModders 原帖存档;
│   │                              mvf.html 只抓到了 Cloudflare 拦截页,无内容)
│   ├── *.ps1                     启动/崩溃诊断辅助脚本(check_crash、evt、proc、
│   │                             test_launch、watch_launch)
│   ├── REVERSE_*.md              引擎逆向笔记(见下)
│   ├── dl/spcomp.exe             SourcePawn 编译器 1.12.0.7255(从官方 SourceMod 包取出,
│   │                             只留构建所需的这一个文件)
│   ├── out/                      逆向与探测过程留下的证据 dump(probe*.txt、
│   │                             crosshair_*、wpn_dump、*_binscan 等)
│   ├── .gitignore                本目录的忽略规则
│   └── src/scripting/            纯构建输入
│       ├── plugins/              **只在编的 16 个模块**的源码(其余已删除,见文首)
│       ├── include/              编译用 SourceMod include = 官方 1.12.0.7255 原样
│       │                         (唯一额外文件是 socket.inc,官方包不含 socket)
│       ├── BMAG/                 merge.py / spcomp 的产物目录 —— **整个目录不入库**
│       └── compile_all.sh        逐个编译 plugins/*.sp 的批处理脚本(路径硬编码,见上)
└── README.md
```

---

## 部署

服务器是 steamcmd 安装的 srcds，根目录记为 `%SRV%`（即含 `srcds.exe` 的那一层）。

**部署前提:一份正常的 SourceMod 1.12 安装。** 请先向 srcds 安装 MetaMod 和 SourceMod。

### 方式 A:用 CI 产出的完整包(推荐)

**仓库里不存放任何 `BMAG.smx` 成品**(它由源码编译而来,理由见[目录结构](#目录结构))。
GitHub Actions 每次 push 都会编一个,而且**artifact 里带上了仓库 `bms/` 的全部内容** ——
所以它本身就是一份完整部署包:

```
BMAG-<sha>.zip
├── bms/                       ← 整个部署树(仓库 bms/ + 这次新编的 BMAG.smx)
└── build.log                  ← 编译日志,部署时可无视
```

对于全新安装，**解压到 `%SRV%\`**，部署即告完成。
如果你已经部署过、只想更新插件，那就只把包里的 `bms/addons/sourcemod/plugins/BMAG.smx` 拷过去。

### 方式 B:本地构建 + 覆盖仓库的 `bms/`

1. 走[从源码构建](build.md#从源码构建),产物在 `smx_analysis/src/scripting/BMAG/BMAG.smx`
2. 把产物移到 plugins 插件目录下:`bms/addons/sourcemod/plugins/`
3. 把 bms 覆盖到 srcds 根目录 %SRV%

覆盖完重启服务器,或控制台 `sm plugins reload BMAG`。

### 启动

```bat
srcds.exe -console -game bms +map dm_boom +maxplayers 16 -condebug
```

日志追加写入 `bms\console.log`。建议让它随开机自动启动(计划任务或服务),
进程没起来时重启即可 —— 见"已知问题"里的启动竞态。

### 其它部署说明

`BMAG.smx` 里没有任何官方插件,管理员、聊天命令、禁言禁麦、投票、娱乐命令等全部由你 `addons/sourcemod/plugins/` 里的官方 `.smx` 提供。
官方插件提供的功能见 [插件#三、官方插件:全部交给用户自己装](modules.md#三官方插件全部交给用户自己装)。

**唯一一条与官方插件的冲突：停用 `nextmap.smx`**。本服换图由 `bms_match` 的投票 + 核心的 `sm_nextmap` 决定，然而 nextmap 插件会按 `mapcyclefile`自动推进，修改 `sm_nextmap`，覆盖投票结果。**在你自己的 SourceMod 安装里**把它从 `plugins/` 挪到 `plugins/disabled/` 下以停用。

**`socket.ext.dll` 是硬依赖,别漏。** `BMAG.smx` 对 socket 扩展是 `autoload = 1` / `required = 1`
—— 缺了它 BMAG 会直接加载失败(`Unable to load plugin … Required extension "Socket" is not
running`)。socket 是 AlliedModders 上**单独分发**的扩展([发布帖](https://forums.alliedmods.net/showthread.php?t=67640)),
**官方 SourceMod 包确实不含它** —— 1.12.0.7255 的 `extensions/` 里没有 `socket.ext.dll`,
`.inc` 也不含 `socket.inc`(已核对),所以仓库必须自己带这一份
(`bms/addons/sourcemod/extensions/socket.ext.dll`)。**别删。**
> 对于 Linux 用户，需要自行添加`socket.ext.so`，理论上现有插件并非 Windows 限定（未测试）

除 `BMAG.smx` 外的四个 `.smx` 是**独立第三方插件,不在 BMAG 里**(清单见
[插件#四、独立插件](modules.md#四独立插件))。其中 `is_weaponfx.smx` 需在 `server.cfg` 里显式设
`is_weaponfix_saddr`(默认值会被当成"未配置"而自我禁用);`is_bms_fix_timelimit.smx`
负责让 `mp_timelimit` 在新地图加载后仍能生效 —— 漏了它,非比赛期间的回合时限就不对。

`translations/` 里那三份短语文件**是运行时读取的,不编进 `BMAG.smx`**
(`bms_match.phrases.txt`、`fast_spawn.phrases.txt`、`spawn_marker.phrases.txt`)。
漏了的话聊天框里所有 `[比赛]` 提示都会显示成短语键名。改文案(不动代码)
只需重传这三个文件 + 换图或 `sm plugins reload BMAG`,不必重新编译。

复制后重启服务器,或在服务器控制台执行 `sm plugins reload BMAG`。
**新增**的独立插件(如 `is_bms_fix_timelimit`)SourceMod 只在地图切换时才自动加载,
要么换一次图,要么控制台 `sm plugins load is_bms_fix_timelimit`。

---

### SDK 版本与升级记录

**当前固定的是 SourceMod 官方最新稳定版 `1.12.0.7255`**（2026-10-02 [`alliedmodders/sourcemod`](https://github.com/alliedmodders/sourcemod/releases/tag/1.12.0.7255)）
`smx_analysis/dl/` 里只留了 `spcomp.exe`(1.1 MB)—— 官方包其余内容(`bin/`、`extensions/`、
`translations/`、官方插件源码)对构建没用,已不再入库;`src/scripting/include/` 就是官方 1.12 的原样 include。
详见[构建#CI](build.md#CI)

---

## 已知问题

- **启动间歇卡死**:Steam 客户端注入的 `crashhandler.dll` 与加载器竞态,约一半概率卡在进程早期(35MB、无端口)。**没有稳的根治办法,用外部脚本兜底** —— 检测 27015 端口,没起来就杀掉进程重启;退出 Steam 后启动大概率一次成功。
- **关窗时退出码 -1073740791**:服务器已走完干净关机(日志已落盘),随后 Steam 的 crashhandler 在清理阶段 fail-fast —— 无害,可忽略。
- **`Unknown command heartbeat`**:Black Mesa 引擎在 `mp_restartgame` 时自发执行 GoldSrc 遗留命令产生的噪音,无害。
- **`bms/cfg/server.cfg` 里有 3 条没有任何模块提供的设置**:`sm_blockcommand "spec_mode 7"`、`sm_downloader_enabled "1"`、`sm_motd_url "..."` —— 全仓库(连自带的 SourceMod 官方包 `smx_analysis/dl/`)都搜不到创建它们的代码,应是原服插件集里没随仓库一起归档的那部分留下的。
  - 前两条会在开服日志里报 `Unknown command`,**不影响运行**,可删可留。
  - `sm_motd_url` 稍特殊:`motd-fixer` 会用 `FindConVar` 读它,但读不到就回退到服务器上的 `bms/cfg/motd.txt`、再回退到默认 MOTD 面板(见 `smx_analysis/src/scripting/plugins/motd-fixer.sp` 的 `OpenMOTD()`)。所以**在你装上创建该 cvar 的插件之前,改它不会生效**,MOTD 实际走的还是服务器上的 `bms/cfg/motd.txt`(本仓库不含该文件)。
- **只有在你把官方插件也停掉的情况下才会看到的 `Unknown command`**:`bms/cfg/server.cfg` 第 58 / 85 / 99
  行用 `sm_say` 播报,而 `sm_say` 由官方插件 `basechat.smx` 提供。BMAG 不含 `basechat`,但
  SourceMod 自带且默认启用 —— **官方插件保持启用就不会有这个报错**;若你手工停用了 `basechat`,
  这三行会报 `Unknown command: sm_say`,可删可留。
  SourceMod 自带的 `configs/adminmenu_sorting.txt` 里列着的 `sm_kick` / `sm_ban` / `sm_slay` 等条目同理,
  那只是排序表,条目对应的命令不存在时会被忽略,无害。
- **管理员名单要在你自己的 SourceMod 安装里配**:`<你的 SourceMod>/configs/admins.cfg` 里的
  `identity` 默认为占位值,必须换成真实 SteamID,否则你没有任何管理员权限。
  本仓库不再附带这个文件(它是 SourceMod 官方安装的一部分),读取它的是官方插件
  `admin-flatfile.smx`(自带、默认启用),BMAG 不参与。
