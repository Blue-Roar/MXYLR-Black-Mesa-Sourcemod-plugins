# Black Mesa SourceMod 插件集

Black Mesa(黑山起源)的 **SourceMod 插件与配置集合**,整理自一台实际在跑的死亡竞赛服务器。
仓库里装了两块**互不依赖**的内容,可以只取其中一块用:

| 部分 | 内容 | 从哪看 |
|---|---|---|
| **① 死亡竞赛服务器**(主体) | 16 个模块合并编译成单个 `BMAG.smx`(全是自研 / 第三方,**不含任何 SourceMod 官方插件**),另有 4 个独立第三方插件单独加载 | [目录结构](#目录结构) · [部署](#部署) · [从源码构建](#五从源码构建) |
| **② 配置** | 服务器 `bms/cfg/`、本项目自己的 SourceMod 配置 `bms/addons/sourcemod/configs/` | [⚠️ 部署前必改清单](#️-部署前必改清单) |

> **想直接开服** → **最快是拿 CI 的完整包**:Actions 里下 `BMAG-<sha>.zip`,解压到 `%SRV%\` 就完事
> (包里 = 仓库 `bms/` + 新编的 `BMAG.smx`)。自己构建也行,见[部署](#部署)。
> 两者都要先过一遍 [⚠️ 部署前必改清单](#️-部署前必改清单):配置里还带着原服的服务器名、群号、域名。
> **想改插件** → [五、从源码构建](#五从源码构建),`merge.py` 把 16 个模块合并成一个 `BMAG.sp` 再交给 spcomp 编译。
> **只想抄某个功能** → [一、`bms_match`](#一bms_match--比赛插件自研) 是自研比赛插件,[二、其它自研模块](#二其它自研--深度改造模块) 列了 9 个深度改造模块。

> **2026-10-04 第二批清理**:BMAG 里原先整合的 **19 个 SourceMod 官方插件已全部移出**
> (35 模块 → 16 模块),**官方插件由用户自己的 SourceMod 安装提供**,详见
> [三、官方插件:全部交给用户自己装](#三官方插件全部交给用户自己装)。这样做是为了**部署零冲突** ——
> 把 `BMAG.smx` 丢进原始 SourceMod 安装即可,不需要停用任何官方插件。
>
> 移出的 19 个里,**18 个与上游官方源码逐字节一致**(当初只是整合进来、没动过);
> 唯一被本地改过的是 `basetriggers`(见下)。`pause` / `showhealth` / `sm_noearbleed`
> 这三个**本来就不是官方插件**,保留在 BMAG 内。
>
> ⚠️ **被移出模块的源码已从本仓库删除**(连同 7 个历史上就没编进来的模块,共 26 个)。
> 现在 `smx_analysis/src/scripting/plugins/` 下**只剩 16 个在编模块的源码**。
> 要重新并入某个官方插件,得自己从上游取源码 —— 唯一需要留意的本地改动是
> **`basetriggers`**:上游在 `OnPluginStart` 里挂 `HookEvent("game_start", Event_GameStart)`,
> 本仓库曾改成 `HookEvent("round_start", Event_GameStart)` 以适配 Black Mesa,
> **这行改动随源码删除,只剩本条记录**(它当前也不生效:BMAG 不编 basetriggers,
> 用户装的是官方原版 `basetriggers.smx`)。

> **单人战役插件已移出本仓库**:`campaign/` 整个目录(tau_mp、hl1tau、`REVERSE_TAU.md`)
> 已不再随本仓库分发,需要它们请翻 `2026-10-04` 之后的提交里删除它们的那次之前的历史。
> **注意**:本仓库仍保留针对「单人战役**地图**」的适配 —— `bms_match` 的 `Bms_IsCampaignMap()`
> 与 `fast_spawn` 的 `FS_Campaign()`(按地图名前缀 `bm_c<数字>` 判定)属于 DM 服务器的一部分,
> 与上面那两个插件无关,没有跟着删。

源码、合并器与逆向笔记全部在本仓库内,可直接重建。

**唯一不入库**的是 `client_mod/`(自定义准星客户端 mod,已搁置)。

---

## 目录

- [⚠️ 部署前必改清单](#️-部署前必改清单)
- [目录结构](#目录结构)
- [部署](#部署) · [启动](#启动) · [RCON](#rcon)
- [权限标志](#权限标志)
- [一、`bms_match` — 比赛插件(自研)](#一bms_match--比赛插件自研)
- [二、其它自研 / 深度改造模块](#二其它自研--深度改造模块)
- [三、官方插件:全部交给用户自己装](#三官方插件全部交给用户自己装)
- [四、独立插件](#四独立插件)
- [五、从源码构建](#五从源码构建)
- [六、已知问题](#六已知问题)

---

## ⚠️ 部署前必改清单

本仓库是从一台**已经在跑的**服务器上整理出来的,配置里仍带着原服的服务器名、
群号、域名、账号和**占位 SteamID**。直接照抄开服,你的服务器会顶着别人的名字、
把玩家引到别人的群和网站,而你本人拿不到任何管理员权限。

下表是全部需要动手的地方;每个文件的顶部也都写了同样的提示,
搜 `>>>` 就能在文件里定位到具体那一行。

| 文件 | 改什么 | 怎么改 |
|---|---|---|
| `bms/cfg/server.cfg` | `hostname`、`sv_region`、`tv_title`/`tv_name`、`maxplayers`、`sv_password` | 改成你自己服务器的信息 |
| `bms/cfg/server.cfg` | `sv_downloadurl`、`sm_motd_url` | 换成你的域名;**没有 FastDL 就把 `sv_downloadurl` 整行注释掉**(玩家回退 srcds 直传,慢但能连)。`sm_motd_url` 需由插件创建才生效 —— 见[已知问题](#六已知问题) |
| `bms/cfg/server.cfg` | `is_weaponfix_saddr` | 填**外网玩家能连到的**公网 `IP:端口`,不能留 `127.0.0.1`,否则武器动画修复静默失效 |
| `bms/cfg/server.cfg` | `rcon_password` | **该文件里没有这一行**,需自行在启动参数加 `+rcon_password "你的密码"`,且**绝不要提交进 git** |
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
| `<你的 SourceMod>/configs/databases.cfg` | 只有用 `clientprefs` 持久化 cookie 时才需要建(里面是数据库密码,本仓库故意不含) |

**不需要改**(照抄即可):`bms/cfg/autoexec.cfg`、`bms/cfg/listenserver.cfg`、
`bms/addons/sourcemod/configs/downloads.ini` 等。

**辅助脚本里的路径也是硬编码的**,换机器要改(不改不影响开服,只影响你跑这些脚本):

| 文件 | 硬编码内容 |
|---|---|
| `smx_analysis/watch_launch.ps1` | `F:\BMServer\srcds.exe`、`F:\BMServer\bms\console.log` |
| `smx_analysis/src/scripting/compile_all.sh` | `SPCOMP="/c/tmp/smx_analysis/dl/..."`(该路径在本仓库里**并不存在**,见 [从源码构建](#五从源码构建)) |

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

`.gitignore` 现在排除四类东西:

| 规则 | 排除什么 |
|---|---|
| `smx_analysis/src/scripting/BMAG/` | **整个构建输出目录**(`BMAG.sp` 与各模块副本由 `merge.py` 生成,`BMAG.smx` 由 spcomp 编译)—— 全部可重建 |
| `bms/addons/sourcemod/plugins/BMAG.smx` | 编译出的成品。**仓库里不入库任何 `BMAG.smx`**;`bms/` 里其余 `.smx` 是要分发的二进制,照常入库 |
| `/dist/`、`smx_analysis/build.log` | CI 构建产物(在 runner 上生成;本地复跑同一套命令时也会出现) |
| `client_mod/`、`REVERSE_CROSSHAIR.md` | 暂时搁置的自定义准星客户端 mod |

下载的工具链与证据 dump(`smx_analysis/dl/`、`smx_analysis/out/`)均已入库留档。

> **为什么 `BMAG.smx` 不入库**:它和「部署树里那份」曾经是同一份东西存两处,而 spcomp
> 不可字节复现(见第五节),重编一次 git 就多一个无意义的二进制 diff。现在仓库只放源码 +
> 配置 + 第三方二进制,**成品来自本地构建或 CI artifact**。

> **2026-10-04 清理**:2022 年上传的原始逐插件 smx(`plugins/<模块名>.smx`)、已被 `BMAG.smx` 取代的
> 旧版平铺产物(`smx_analysis/plugins/`、`smx_analysis/partial.sp`、`smx_analysis/bctest.smx`)
> 以及与本目录内容重复的 `bms_match_delivery.7z` 已从仓库移除(共 87 个文件 / 约 1.2 MB)。
> 当前构建与部署都不依赖它们:`merge.py` 合并的是 `src/scripting/plugins/` 下的源码,
> `bisect_compile.py` 的 `partial.sp` 是运行时生成而非读取仓库里那份。
> 需要查旧版逐插件产物时,翻 `2026-10-04` 之前的提交历史即可。

> **旧交付包 `bms_match_delivery/` 已删除**。它是 2026-08-23 那次交付的快照,
> 里面的 `BMAG.smx` 是 292,367 字节(**41 模块**时代,比当前落后两个大版本 —— 当前 99,104 字节 / 16 模块),
> `bms_match.cfg`、`bms_webpanel.html`、`mapcycle_*.txt`、`server_match*.cfg`、
> `bms_match.phrases.txt` 也都是更早的版本。删之前逐文件与当前版本核对过:
> 没有独有内容会因此丢失,唯一有实质差异的 `tv_enable 1` 当前已在 `bms/cfg/server.cfg` 里设置,
> 里面的 `socket.ext.dll` 已移入 `bms/addons/sourcemod/extensions/`,其余 18 个文件均为重复。


### 逆向笔记(`smx_analysis/REVERSE_*.md`)

这些文档记录了本仓库所有非平凡修改所依据的引擎级证据(反汇编地址、签名、调用链),**改动相关代码前请先读**:

| 文件 | 内容 |
|---|---|
| `REVERSE_RESPAWN.md` | 死亡竞赛重生机制、复活点选择为何失效 |
| `REVERSE_TIMER.md` | 回合计时器与 `mp_restartgame` 通道 |
| `REVERSE_VGUI.md` | VGUIMenu 面板与无线电菜单 |
| `REVERSE_WALLPEN.md` | 弹道穿墙与玻璃穿透 |

> `REVERSE_TAU.md`(tau 炮单人/多人分支、高斯跳、跌落伤害链路)曾随单人战役插件放在 `campaign/tau_mp/` 下,
> **现已随该目录一起移出本仓库**。`REVERSE_WALLPEN.md` 里对它的引用保留为历史说明。

---

## 部署

服务器是 steamcmd 安装的 srcds,根目录记为 `%SRV%`(即含 `srcds.exe` 的那一层)。

### 方式 A:用 CI 产出的完整包(推荐)

**仓库里不存放任何 `BMAG.smx` 成品**(它由源码编译而来,理由见[目录结构](#目录结构))。
GitHub Actions 每次 push 都会编一个,而且**artifact 里带上了仓库 `bms/` 的全部内容** ——
所以它本身就是一份完整部署包:

```
BMAG-<sha>.zip
├── bms/                       ← 整个部署树(仓库 bms/ + 这次新编的 BMAG.smx)
└── build.log                  ← 编译日志,部署时可无视
```

**解压到 `%SRV%\`,部署就完成了。** 与方式 B 的区别只是「连配置和 `cfg/` 一起覆盖」;
如果你已经部署过、只想更新插件,那就只把包里的
`bms/addons/sourcemod/plugins/BMAG.smx` 拷过去。

### 方式 B:本地构建 + 覆盖仓库的 `bms/`

1. 走[五、从源码构建](#五从源码构建),产物在 `smx_analysis/src/scripting/BMAG/BMAG.smx`
2. 把它拷进部署树:`copy /Y smx_analysis\src\scripting\BMAG\BMAG.smx  bms\addons\sourcemod\plugins\`
3. 覆盖到服务器:

```bat
set SRV=<你的 srcds 根目录>
xcopy /E /Y /I bms  %SRV%\bms\
```

`xcopy /E` 会连同子目录一起复制并覆盖同名文件;只想先看会动哪些文件就加 `/L` 干跑一遍。
覆盖完重启服务器,或控制台 `sm plugins reload BMAG`。

> ⚠️ 第 2 步别漏。`bms/addons/sourcemod/plugins/BMAG.smx` 是 gitignore 的,
> **在全新克隆的仓库里它不存在** —— 直接 `xcopy bms`(没先构建)会漏掉插件本体。

`bms/` 里各类文件落到服务器上的位置:

| 仓库路径 | 服务器路径 | 内容 |
|---|---|---|
| `bms/addons/sourcemod/plugins/` | `%SRV%\bms\addons\sourcemod\plugins\` | `BMAG.smx`(**需自行产出**)+ 4 个第三方 `.smx`(`disabled/` 下 1 个是停用件) |
| `bms/addons/sourcemod/translations/` | `…\addons\sourcemod\translations\` | 3 份短语文件 |
| `bms/addons/sourcemod/configs/` | `…\addons\sourcemod\configs\` | 本项目自己的配置:`bms_match.cfg`、`bms_webpanel.html`、`advertisements.txt`、`downloads*.ini` |
| `bms/addons/sourcemod/extensions/` | `…\addons\sourcemod\extensions\` | `socket.ext.dll` |
| `bms/cfg/` | `%SRV%\bms\cfg\` | 服务器 cfg + 地图池 + 比赛用 cfg |

> **部署前提:一份正常的 SourceMod 安装。** `BMAG.smx` 里没有任何官方插件,管理员、聊天命令、
> 禁言禁麦、投票、娱乐命令等全部由你 `addons/sourcemod/plugins/` 里的官方 `.smx` 提供 ——
> **保持它们原样即可,不需要停用任何一个**(BMAG 与它们零重叠)。哪些官方插件提供什么功能,
> 见 [三、官方插件:全部交给用户自己装](#三官方插件全部交给用户自己装)。

> **`socket.ext.dll` 是硬依赖,别漏。** `BMAG.smx` 对 socket 扩展是 `autoload = 1` / `required = 1`
> —— 缺了它 BMAG 会直接加载失败(`Unable to load plugin … Required extension "Socket" is not
> running`)。socket 是 AlliedModders 上**单独分发**的扩展([发布帖](https://forums.alliedmods.net/showthread.php?t=67640)),
> **官方 SourceMod 包确实不含它** —— 1.12.0.7255 的 `extensions/` 里没有 `socket.ext.dll`,
> `.inc` 也不含 `socket.inc`(已核对),所以仓库必须自己带这一份
> (`bms/addons/sourcemod/extensions/socket.ext.dll`)。**别删。**

> 除 `BMAG.smx` 外的四个 `.smx` 是**独立第三方插件,不在 BMAG 里**(清单见
> [四、独立插件](#四独立插件))。其中 `is_weaponfx.smx` 需在 `server.cfg` 里显式设
> `is_weaponfix_saddr`(默认值会被当成"未配置"而自我禁用);`is_bms_fix_timelimit.smx`
> 负责让 `mp_timelimit` 在新地图加载后仍能生效 —— 漏了它,非比赛期间的回合时限就不对。

> `translations/` 里那三份短语文件**是运行时读取的,不编进 `BMAG.smx`**
> (`bms_match.phrases.txt`、`fast_spawn.phrases.txt`、`spawn_marker.phrases.txt`)。
> 漏了的话聊天框里所有 `[比赛]` 提示都会显示成短语键名。改文案(不动代码)
> 只需重传这三个文件 + 换图或 `sm plugins reload BMAG`,不必重新编译。

> **唯一一条与官方插件的功能性(非冲突性)取舍:停用 `nextmap.smx`**。
> 本服换图由 `bms_match` 的投票 + 核心的 `sm_nextmap` 决定;nextmap 插件会按 `mapcyclefile`
> 自动推进 `sm_nextmap`,和投票结果打架。它不影响加载,只是会让 `sm_nextmap` 被偷偷改掉 ——
> 要不要停用取决于你。**在你自己的 SourceMod 安装里**把它从 `plugins/` 挪到 `plugins/disabled/`
> (本仓库不再附带那份副本)。
> (注:`SetNextMap` / `GetNextMap` 是 **SourceMod 核心**提供的 native,不是 nextmap.smx ——
> 所以停用它**不会**让 BMAG 加载失败。)

> **单人战役的 `tau_mp` / `hl1tau` 已不在本仓库**(见文首说明)。它们要装的是另一套
> `addons/sourcemod`(Steam 客户端目录下的 Black Mesa),与本仓库的 `bms/` 覆盖树无关 ——
> 这里不再提供安装步骤。

复制后重启服务器,或在服务器控制台执行 `sm plugins reload BMAG`。
**新增**的独立插件(如 `is_bms_fix_timelimit`)SourceMod 只在地图切换时才自动加载,
要么换一次图,要么控制台 `sm plugins load is_bms_fix_timelimit`。

### 启动

```bat
srcds.exe -game bms +map dm_boom +maxplayers 16 -condebug
```

日志追加写入 `bms\console.log`。建议让它随开机自动启动(计划任务或服务),
进程没起来时重启即可 —— 见"已知问题"里的启动竞态。

### RCON

`rcon_password` 需自行在**启动参数**里设置(例如 `+rcon_password "你的密码"`),
**不随本仓库分发**,`bms/cfg/server.cfg` 里也没有这一行 —— 历史上曾经把密码写进该文件
并提交过,所以现在刻意不提供,避免再次泄露。
仓库内的调试客户端从环境变量读取连接信息:

```bash
RCON_HOST=127.0.0.1 RCON_PORT=27015 RCON_PASSWORD='<你的rcon密码>' python smx_analysis/rcon.py "sm plugins list"
```

客户端超时建议 ≥25 秒(该引擎 RCON 响应较慢)。

---

## 权限标志

下表用标志字母表示权限,与 SourceMod 的 `configs/admin_levels.cfg` 一致
(该文件由你自己的 SourceMod 提供,本仓库不附带):

| 字母 | 权限 | 字母 | 权限 | 字母 | 权限 |
|---|---|---|---|---|---|
| a | 预留通道 | f | 处死 | k | 发起投票 |
| b | 通用管理 | g | 换图 | l | 设密码 |
| c | 踢人 | h | 修改 ConVar | m | RCON |
| d | 封禁 | i | 执行配置文件 | n | 作弊 |
| e | 解封 | j | 管理员聊天 | z | ROOT |

> `o`–`t` 是留给自定义权限用的空位,本仓库未占用。

聊天中输入 `!<命令>` 或 `/<命令>` 即可触发;控制台输入命令原名。

---

## 一、`bms_match` — 比赛插件(自研)

参考 hl2dm 的 xms 比赛插件、按 Black Mesa 引擎重写的比赛系统。
是 `BMAG.smx` 的一个模块,**不支持单独加载**。
(xms 本身已不在本仓库 —— 见第四节末尾。)

### 玩家命令

| 命令 | 说明 |
|---|---|
| `!start` | 开始比赛。人数达到 `VoteMinPlayers` 时发起投票;否则(含 bot 时至少 2 人)直接开始 |
| `!cancel` | 取消比赛并恢复公服参数。比赛中需投票通过 |
| `!help` / `!commands` | 弹出比赛指令菜单(无线电菜单形式) |
| `!maplist` / `!list [模式]` | 查看地图池,`ffa` / `tdm` / `all`,默认当前模式 |
| `!run <地图>` / `!runnow <地图>` | 发起"换当前图"投票,支持 `模式:地图` 与缩写 |
| `!runnext <地图>` | 发起"设置下一张图"投票 |
| `!runrandom` | 从当前模式地图池随机抽 4 张发起换图投票 |
| `!shuffle` | 洗牌分队(仅 TDM) |
| `!invert` | 互换两队(仅 TDM) |
| `!yes` / `!no` / `!1`–`!5` | 投票表决 |
| `!pause` / `!unpause` | 暂停 / 继续服务器 |
| `!panel` / `!webpanel` | 打开游戏内网页控制台(见下) |
| `!vguitest` | 弹出测试用 VGUI 面板(比分板/隐藏变体,调试用) |

> `!pause` / `!unpause` 分两种情形:**比赛内**由 `bms_match` 自己接管(它直接发
> `ServerCommand("pause")` 并同步比赛状态机);**非比赛状态**下 `bms_match` 放行,由 SourceMod 核心
> 把 `!pause` 转成 `sm_pause` 交给 `pause` 模块(第三方插件 ddhoward `[Any?] Pause The Game`,
> 仍嵌在 `BMAG.smx` 内)。两者不要混用。

**聊天别名**:`!stop` → `!cancel`、`!join` → 加入人数较少的队伍、`!spec` → 观战、
`!next <图>` → `!runnext <图>`、`!random` → `!runrandom`。

`!run` 支持的地图缩写:`bunker`→`dm_lambdabunker`、`bounce`、`stalk`→`dm_stalkyard`、
`sub`→`dm_subtransit`、`gas`→`dm_gasworks`、`rail`、`crossfire`、`boom`。

### 管理员命令(需 b = 通用管理)

| 命令 | 说明 |
|---|---|
| `!forcespec <玩家>` | 强制某玩家转入观战 |
| `!allow <玩家>` | 放行某玩家加入比赛(解除开赛后的加入封锁) |
| `!starttest` | 启动一场 **1 分钟**的测试比赛,用于验证 SourceTV 录像链路 |

### ConVar

| ConVar | 默认 | 说明 |
|---|---|---|
| `sm_bms_webpanel_enabled` | 1 | 启用游戏内网页控制台(需要 socket 扩展) |
| `sm_bms_webpanel_host` | *(空)* | 面板 URL 中使用的 Host,留空 = `127.0.0.1` |
| `sm_bms_webpanel_port` | 28015 | 网页控制台监听端口 |

### 命令监听(拦截引擎命令)

插件挂在这些引擎命令上,按比赛状态放行或吞掉:

| 命令 | 比赛中的行为 |
|---|---|
| `jointeam` / `spectate` / `chooseteam` | 开赛后封锁换边;经 `!allow` 放行 |
| `pause` / `unpause` / `setpause` | 暂停状态与比赛状态机同步;吞掉引擎自身的回显以免二次派发 |
| `kill` / `explode` | 倒计时与赛后结算阶段禁止自杀绕过冻结 |
| `changelevel` / `changelevel_next` | 比赛中阻止手动换图,由插件统一发起投票 |

### 比赛流程

1. `!start` → 人数 < `VoteMinPlayers` 直接开始,否则发起投票
2. 进入 MatchWait:执行 `exec server_match`(重置时限/封顶/复活)→ 冻结玩家并剥离武器 → 4 秒倒计时
3. 进入 Match:计时开始,锁定队伍;参赛者掉线自动暂停;FFA 取最高击杀(平局比死亡数),TDM 比队伍分
4. 平分 → 自动加时(Overtime,每分钟续时直到分出胜负)
5. 结束:广播胜利与比分 → `exec server_match_post` 恢复公服参数 → 自动发起下一张图投票 → 引擎自然换图

比赛自动开启 SourceTV 录像,文件落在服务器本机的 `demos\` 目录(不提供下载)。

**单人战役地图会被自动跳过**:判据是地图名前缀 `bm_c<数字>`(78 张战役图全部命中,与 DM 图无冲突)。
命中时跳过队伍枚举、静默 1Hz 定时器、并关闭 `fast_spawn`。

### 配置(`bms/addons/sourcemod/configs/bms_match.cfg`)

| 键 | 默认 | 说明 |
|---|---|---|
| `VoteMinPlayers` / `VoteMaxTime` / `VoteCooldown` | 3 / 25 / 30 | 投票人数门槛、时限、冷却(秒) |
| `AutoVoting` | 1 | 比赛结束自动发起下一图投票 |
| `DefaultMode` / `RetainModes` | ffa / ffa,tdm | 默认模式 / 换图后保留的模式 |
| `PreMatchCommand` / `PostMatchCommand` | `exec server_match` / `exec server_match_post` | 开赛 / 赛后执行的 cfg |
| `Gamemodes` | — | 每模式:`Command`(如 `mp_teamplay 0`)、`Mapcycle`、`Defaultmap`、`Matchable`、`Overtime`、`MatchTimelimit` |
| `Maps` | — | `StripPrefix`(显示时去掉的图名前缀)、`DefaultModes`(通配映射)、`Abbreviations`(图名缩写) |

地图池文件放在 `bms/cfg/` 下,由各模式的 `Mapcycle` 键引用。`ffa` 与 `tdm` 各 12 张官方 DM 图,
两份名单当前完全相同:
`dm_boom`、`dm_bounce`、`dm_chopper`、`dm_crossfire`、`dm_gasworks`、`dm_lambdabunker`、
`dm_power`、`dm_rail`、`dm_stack`、`dm_stalkyard`、`dm_subtransit`、`dm_undertow`。

---

## 二、其它自研 / 深度改造模块

以下 9 个模块都**编译在 `BMAG.smx` 内部**(见 [五、从源码构建](#五从源码构建)),不能单独加载。
`spawn_distribute`、`textmsg_fix` 为自研;其余基于 AlliedModders 社区插件,按本服需要做过适配或实质改造
(`fast_spawn`、`speclist` 源自 Alienmario,`SpecDetails` 源自 wribit,`missing_viewmodel_fix` 源自 ch4os + SHUFEN,
`advertisements` 源自 Tsunami;各文件头部保留原作者声明)。

| 模块 | 一句话 | 详见 |
|---|---|---|
| `fast_spawn` | 零秒重生,不等原生按键或 5 秒 `mp_forcerespawn` | 下节 |
| `spawn_distribute` | 复活点均匀分配,修原生同点堆人 | 下节 |
| `textmsg_fix` | CP936 下 UTF-8 中文消息导致的 `_vsnprintf` 崩溃 | 下节 |
| `adv-weapon_cleaner` | 掉落武器清扫 | 下节 |
| `SpecDetails` | 观察者详情 | 下节 |
| `speclist` | 观战者列表 | 下节 |
| `missing_viewmodel_fix` | 切队/切观察后重建 viewmodel | 下节 |
| `advertisements` | 轮播广告 | 下节 |
| `sm_noearbleed` | 去掉爆炸耳鸣/压耳声 | 下节 |

### `fast_spawn` — 零秒重生

死亡后立即重生,不等原生按键或 5 秒 `mp_forcerespawn`。

| 命令 | 权限 | 说明 |
|---|---|---|
| `fastspawn` / `sm_fs` | b | 查询或开关零秒重生 |

| ConVar | 默认 | 说明 |
|---|---|---|
| `sm_fastspawn` | 1 | 启用:死亡 `sm_fastspawn_time` 秒后重生 |
| `sm_fastspawn_batch` | 4 | 每个游戏 tick 最多重生几人(削平爆发重生;调小更平滑) |
| `sm_fastspawn_time` | 0.0 | 重生延迟秒数(0 = 立即) |

行为要点:

- 真人走 `OnPlayerRunCmd` 判定,`DispatchSpawn` 推迟到下一帧(避免在移动循环中途重入 `Spawn()` 导致"原地复活")
- bot 绕过 `OnPlayerRunCmd`,用 0.1 秒 timer 轮询模拟按键
- 致死伤害(`damage >= 血量`)时**先剥光武器再死**,避免掉落武器堆积;重生时给玩家加一帧 `FL_NOTARGET` 防止默认装备掉地上
- **单人战役地图与比赛期间自动关闭**(见 `bms_match` 一节):比赛期保留正常武器掉落,战役图避免误判高斯跳落地为致死

> 本服 `bms/cfg/server.cfg` 里显式设了 `sm_fastspawn 1` + `sm_fastspawn_time 0.0`(即最激进档)。

### `spawn_distribute` — 复活点均匀分配

BM 引擎原生的复活点选择链已损坏(`IsSpawnPointValid` 不读标旗、用零长度 trace 判定占用),
导致所有人被扔到同一个点。本模块不碰原生逻辑,在 `player_spawn` 事件里自己挑空闲点传送。

| ConVar | 默认 | 说明 |
|---|---|---|
| `spawn_distribute_enabled` | 1 | 开启(1 = 在 `player_spawn` 时挑空闲复活点传送) |
| `spawn_distribute_cooldown` | 2.0 | 同一点被分配后多少秒内不重复分配(0 = 关闭时间占用判定) |
| `spawn_distribute_radius` | 64.0 | 真人占用判定半径;范围内有**其他真人**即视为占用(bot 不参与) |

### `textmsg_fix` — 中文崩溃修复

修复 CP936 代码页下 UTF-8 中文消息尾字节悬空前导导致的 `_vsnprintf` fail-fast 崩溃。
无命令、无 ConVar,纯 Hook。

### `adv-weapon_cleaner` — 掉落武器清扫

| ConVar | 默认 | 说明 |
|---|---|---|
| `adv_weapon_cleaner_keep_map_weapons` | 1 | 是否保留地图固有武器(0 = 清,1 = 留) |
| `adv_weapon_cleaner_much_weapons` | 100 | 触发清理的武器数阈值(含玩家背包) |
| `adv_weapon_cleaner_remove_delay` | 20.0 | 玩家丢下武器后等待多久移除 |
| `adv_weapon_cleaner_remove_delay2` | 0.1 | 每把武器的递减延迟 |
| `adv_weapon_cleaner_sweep_interval` | 10.0 | 全量清扫间隔秒数(0 = 关闭清扫) |
| `adv_weapon_cleaner_version` | 1.0 | 版本号 |

只跟踪 `weapon_*`,不误删 `item_*`(充电器、道具)。判定依据是 `m_bRemoveable` 数据表字段。

### `SpecDetails` — 观察者详情

| ConVar | 默认 | 说明 |
|---|---|---|
| `sm_specDetails_enabled` | 1 | 启用/关闭本插件 |

比赛期间自动禁用(避免面板风暴;面板更新有 5 秒冷却)。

### `speclist` — 观战者列表

无命令、无 ConVar。定时刷新观战者名单显示。

### `missing_viewmodel_fix` — 缺失持枪模型修复

无命令、无 ConVar。挂 `jointeam` 与 `client_specmode` 监听,在切换队伍/观察模式后重建 viewmodel。
参考来源存档在 `smx_analysis/mvf_wb.html`(AlliedModders 原帖)。

### `advertisements` — 轮播广告

| 命令 | 权限 | 说明 |
|---|---|---|
| `sm_advertisements_reload` | b | 重新读取广告文件 |

| ConVar | 默认 | 说明 |
|---|---|---|
| `sm_advertisements_enabled` | 1 | 启用/关闭广告显示 |
| `sm_advertisements_file` | advertisements.txt | 广告文本文件 |
| `sm_advertisements_interval` | 30 | 广告间隔秒数 |
| `sm_advertisements_random` | 0 | 随机顺序播放 |

> 本服 `bms/cfg/server.cfg` 里把 `sm_advertisements_interval` 改成了 **600**(10 分钟一条),
> 不是上面表里的插件默认值 30。

### `sm_noearbleed` — 去除耳鸣/压耳声

无命令,仅 `sm_noearbleed_version`。挂 `OnTakeDamage` 把 `DMG_BLAST` 改成 `DMG_GENERIC` 以去掉爆炸耳鸣效果(不改伤害数值)。
来源:GitHub `foobarhl/sourcemod` —— 第三方社区插件,**不是 SourceMod 官方插件**,上游官方包里没有对应源码。

---

## 三、官方插件:全部交给用户自己装

### 设计原则

**`BMAG.smx` 里不包含任何一个 SourceMod 官方插件。** 官方插件(admin-flatfile、adminmenu、
adminhelp、basechat、basecomm、basecommands、basevotes、funcommands、playercommands、
rockthevote、mapchooser、clientprefs、antiflood、sounds、reservedslots、sql-admin-manager、
admin-sql-*、nominations、randomcycle、basebans …)**由用户自己的 SourceMod 安装提供**,
本仓库不重复打包。

这样做的好处是**部署零冲突**:把 `BMAG.smx` 丢进一个**原始的 SourceMod 安装**(官方插件该开的开着、
该在 `plugins/disabled/` 的放着),不会出现同名命令被两边注册、admin 菜单分类重名之类的撞车,
**不需要停用任何官方插件**。

BMAG 只负责 SourceMod 不自带的那部分:自研模块([一](#一bms_match--比赛插件自研)、[二](#二其它自研--深度改造模块))
与第三方插件(下表)。

### 编在 `BMAG.smx` 里、且官方包没有的(6 个)

| 模块 | 作用 | 备注 |
|---|---|---|
| `admincheats` | `sm_admin_cheats_level` 控制执行作弊命令所需权限 | 社区插件(devicenull),官方包不含 |
| `connectmessage` | 玩家加入/离开时聊天框提示 | 社区插件 |
| `motd-fixer` | 延时打开 MOTD(引擎自带 MOTD 触发有时序问题) | 社区插件;用 `clientprefs.ext` 的 cookie 记偏好 |
| `pause` | 暂停/继续服务器(`sm_pause` / `sm_unpause` / `sm_setpause`) | **第三方插件**(ddhoward `[Any?] Pause The Game` 18.0114.0)。它只注册 `sm_*` 命令并挂引擎 `pause` 命令监听;聊天里的 `!pause` 由 **SourceMod 核心**把 `!x` 转成 `sm_x` 触发,不依赖 `basechat`。比赛内 `!pause` / `!unpause` 由 `bms_match` 接管,两者不要混用 |
| `showhealth` | 屏幕上显示血量(`sm_show_health` / `sm_show_health_on_hit_only` / `sm_show_health_text_area`) | **第三方插件**;用 `clientprefs.ext` 的 cookie 记"关掉血量显示"的偏好 |
| `teamjoinblocker` | 换边封锁(`sm_toggle_join` / `sm_a`) | 社区插件 |

### 交给用户自己装的官方插件(19 个)

以下模块原本嵌在 `BMAG.smx` 里,**现已全部移出**;它们的源码也**已从本仓库删除**
(想重新合并的话见本节末尾的注意事项)。

「官方包状态」一列指 SourceMod 官方压缩包里 `addons/sourcemod/plugins/` 的默认位置 ——
**`plugins/` = 装完就启用**;**`plugins/disabled/` = 装完是停用的,要用得自己挪出来**。

| 模块 | 提供什么 | 官方包状态 |
|---|---|---|
| `admin-flatfile` | 从管理员名单读管理员 —— **仓库里那份配置就是给它用的,必须启用它才有管理员** | `plugins/` |
| `adminhelp` | `sm_help` / `sm_searchcmd` | `plugins/` |
| `adminmenu` | `sm_admin` 管理员菜单 | `plugins/` |
| `antiflood` | 聊天刷屏限制(`sm_flood_time`) | `plugins/` |
| `basechat` | `sm_say` / `sm_csay` / `sm_hsay` / `sm_msay` / `sm_tsay` / `sm_chat` / `sm_psay`(`bms/cfg/server.cfg` 第 58 / 85 / 99 行用到 `sm_say`) | `plugins/` |
| `basecomm` | 禁言/禁麦(`sm_gag` / `sm_mute` / `sm_silence` 及解除) | `plugins/` |
| `basecommands` | `sm_kick` / `sm_map` / `sm_cvar` / `sm_rcon` / `sm_execcfg` / `sm_cancelvote` / `sm_who` / `sm_reloadadmins` | `plugins/` |
| `basetriggers` | 聊天触发词(`timeleft` / `nextmap` / `motd` / `ff`) | `plugins/` |
| `basevotes` | `sm_vote` / `sm_voteban` / `sm_votekick` / `sm_votemap` | `plugins/` |
| `clientprefs` | 客户端 cookie 界面(`sm_cookies` / `sm_settings`) | `plugins/` |
| `funcommands` | 娱乐命令(`sm_beacon` / `sm_blind` / `sm_burn` / `sm_drug` / `sm_freeze` / `sm_gravity` / `sm_noclip` 等) | `plugins/` |
| `funvotes` | 娱乐投票(`sm_votealltalk` / `sm_voteburn` / `sm_voteff` / `sm_votegravity` / `sm_voteslay`) | `plugins/` |
| `playercommands` | `sm_slap` / `sm_slay` / `sm_rename` | `plugins/` |
| `reservedslots` | 预留通道(`sm_reserve_*` / `sm_hide_slots`) | `plugins/` |
| `sounds` | `sm_play` 播放声音 | `plugins/` |
| `mapchooser` | 结束换图投票、`sm_setnextmap` / `sm_mapvote`、`EndOfMapVoteEnabled()` 等 native | ⚠️ `plugins/disabled/` |
| `nominations` | 地图提名(`sm_nominate`) | ⚠️ `plugins/disabled/` |
| `rockthevote` | RTV 换图(`sm_rtv`) | ⚠️ `plugins/disabled/` |
| `sql-admin-manager` | SQL 管理员增删改(`sm_sql_*`) | ⚠️ `plugins/disabled/` |

> **只影响一个地方**:`advertisements` 会调 `EndOfMapVoteEnabled()` / `HasEndOfMapVoteFinished()`
> 来避开结束换图投票。这两个 native 由 **`mapchooser.smx`** 提供,而它在官方包里默认停用 ——
> 所以 `BMAG.smx` 把这条插件依赖做成了**软依赖**(见下),没启用 mapchooser 也能正常加载,
> 只是 `advertisements` 的那段检查会被跳过。想让结束换图投票真正生效就把 `mapchooser.smx` 挪出来。

### `BMAG.smx` 的依赖形态

移出这 19 个之后,BMAG 对**插件**的依赖只剩一条,而且是软的:

| 依赖 | 类型 | 说明 |
|---|---|---|
| clientprefs.ext / geoip.ext / sdktools.ext / sdkhooks.ext | 扩展,硬依赖 | SourceMod 官方包自带(1.12 已核对) |
| socket.ext | 扩展,**硬依赖** | ⚠️ **官方包不含**,必须随本仓库分发(见部署一节) |
| `mapchooser` | 插件库,**软依赖**(`required = 0`) | `merge.py` 在 `#include <mapchooser>` 前 `#undef REQUIRE_PLUGIN`,使 `SharedPlugin` 块编译成 `required = 0` 并让 include 生成 `__pl_mapchooser_SetNTVOptional()`,把 9 个 mapchooser native 全部标记为可选 |

核对方式(可复现):解压 `BMAG.smx` 的 section 后,`adminmenu` / `basecomm` / `topmenus`
的引用数为 **0**,`__pl_mapchooser` 结构体里的 `required` 字段是 `0`,
`GetAdminTopMenu` / `AddTargetsToMenu` / `BaseComm_*` 全部不再被引用。

### `include/` 的三行本地补丁已还原

`smx_analysis/src/scripting/include/` 过去有 **3 个文件各被改过 1 行** —— 把 `SharedPlugin` 的
`file` 字段从官方名指向 `BMAG.smx`,因为当时这些 native 由 BMAG 自己提供:

| 文件 | 曾经是 | 现在是(= 官方原文) |
|---|---|---|
| `adminmenu.inc` | `file = "BMAG.smx"` | `file = "adminmenu.smx"` |
| `basecomm.inc` | `file = "BMAG.smx"` | `file = "basecomm.smx"` |
| `mapchooser.inc` | `file = "BMAG.smx"` | `file = "mapchooser.smx"` |

现在这三个插件都在 BMAG 之外,补丁已还原。**`include/` = 官方 SourceMod 1.12.0.7255 原样**,
唯一额外文件是 `socket.inc`(官方包不含 socket 扩展,见部署一节)。

> ⚠️ **把官方插件重新加回 `MODULES` 之前先读这段**。合并编译会把模块对
> `adminmenu.inc` / `mapchooser.inc` native 的调用改写成对**同一插件内**对应模块函数的直接调用,
> 这靠 `merge.py` 的 `API_INCLUDES` 驱动(现在是空列表)。要让某个官方插件重新并入,必须:
> ① **先从上游 SourceMod 取回它的源码**(本仓库里的副本已删除)放进 `src/scripting/plugins/`;
> ② 把模块名加回 `MODULES`;③ 把它的 include 名加回 `API_INCLUDES`;
> ④ 把对应 `.inc` 的 `file` 字段改回 `"BMAG.smx"`;⑤ 确认没有同名官方 `.smx` 还开着。
> 少做一步的后果:**编译照样通过,但 `BMAG.smx` 加载时找不到 native 而整插件失效**。
> (②③④ 只对 `adminmenu` / `mapchooser` / `basecomm` 这类提供 native 的插件才需要 ——
> 纯命令类插件如 `funcommands`、`playercommands` 加回 ①② 即可。)

> **`sm_cexec` 本来就不在本仓库里**:它既没有 `.sp` 源码也没有 `.smx`,
> 与 `sm_blockcommand`、`sm_downloader_enabled`、`sm_motd_url` 一样属于原服插件集里没归档的那部分(见[已知问题](#六已知问题))。

---

## 四、独立插件

> **单人战役插件 `tau_mp` / `hl1tau` 已移出本仓库**,本节不再包含它们;
> 原先随它们一起的签名文件 `tau_mp.games.txt` 与逆向笔记 `REVERSE_TAU.md` 也一并移出。

### `spawn_marker.smx` — 复活点标记(**默认停用**)

训练用工具:在 `player_spawn` 时标记真实落点。

| 命令 | 权限 | 说明 |
|---|---|---|
| `sm_spawnmarker` | b | 开关复活点标记 |
| `sm_spawnmap` | b | 开关全图复活点常显 |
| `sm_sm` | b | 快捷别名 |

| ConVar | 默认 | 说明 |
|---|---|---|
| `sm_spawnmarker_enabled` | 0 | 启用敌方复活点标记(0 = 关) |
| `sm_spawnmarker_life` | 5.0 | 标记存在时长(秒) |
| `sm_spawnmarker_spawnmap` | 0 | 持续显示所有死亡竞赛复活点 |

### 第三方插件(无源码)

| 插件 | 作用 |
|---|---|
| `bms_rpgReloadFix.smx` | RPG 换弹动画修复 |
| `bms_weapon_tauStuckFix.smx` | tau 低弹药卡枪修复:右键按下第一 tick 且手持 `weapon_tau` 时把备用弹药补到 3 |
| `is_weaponfx.smx` | 武器动画预热:玩家入服后假连 `is_weaponfix_saddr` 预缓存动画再重连(需在 `server.cfg` 显式设该地址,默认值会被视为"未配置"而自我禁用) |
| `is_bms_fix_timelimit.smx` | 回合时限/倒计时修复(BM 只在地图加载时读一次 `mp_timelimit`,运行期 `SetInt` 无效;它走 `mp_round_time` 实体的加时输入 —— `bms_match` 的计时器沿用同一机制) |

### 已删除源码、不再编入 BMAG 的模块(26 个)

这些模块**既不在 `merge.py` 的 `MODULES` 列表里(不编进 `BMAG.smx`),
源码也已从 `smx_analysis/src/scripting/plugins/` 删除**。
要重新使用,按下面「从哪拿」一列自行获取;`basebans` / `spawn_cap` / `admin-sql-*` 等上游也没有的,只能翻本仓库的提交历史。

| 模块 | 为什么不在 BMAG 里 | 从哪拿 |
|---|---|---|
| `basebans` | 封禁命令(本地封禁,不依赖数据库);原先停放在 `plugins/disabled/basebans.smx` 的那份也已删除 | 上游 SourceMod |
| `nextmap` | 换图由 `bms_match` 的投票 + SourceMod 核心的 `sm_nextmap` 负责(该停用副本已随官方配置一起从仓库移除) | 上游 SourceMod |
| `randomcycle` | 同上,随机换图走 `bms_match` 的 `!runrandom` | 上游 SourceMod |
| `spawn_cap` | 功能已被 `spawn_distribute` 取代(且原版会踢 bot) | 仅本仓库历史 |
| `spawn_marker` | 训练用工具,见上一节;默认停用(**它的 `.smx` 仍在 `plugins/disabled/` 里发**,只是不能再从源码重建) | 仅本仓库历史 |
| `admin-sql-prefetch` | SQL 管理员预取 | 上游 SourceMod |
| `admin-sql-threaded` | SQL 管理员 | 上游 SourceMod |
| `admin-flatfile` | 官方插件 —— 由用户自己的 SourceMod 提供(`plugins/`,默认启用) | 上游 SourceMod |
| `adminhelp` | 官方插件(`plugins/`) | 上游 SourceMod |
| `adminmenu` | 官方插件(`plugins/`) | 上游 SourceMod |
| `antiflood` | 官方插件(`plugins/`) | 上游 SourceMod |
| `basechat` | 官方插件(`plugins/`) | 上游 SourceMod |
| `basecomm` | 官方插件(`plugins/`) | 上游 SourceMod |
| `basecommands` | 官方插件(`plugins/`) | 上游 SourceMod |
| `basetriggers` | 官方插件(`plugins/`);**剔掉的这份曾带一处 Black Mesa 适配(`game_start` → `round_start`),该改动只剩记录、源码已删** | 上游 SourceMod(适配需自己重做) |
| `basevotes` | 官方插件(`plugins/`) | 上游 SourceMod |
| `clientprefs` | 官方插件(`plugins/`);`motd-fixer` / `showhealth` 需要的 cookie native 来自 `clientprefs.ext`,不依赖这个插件 | 上游 SourceMod |
| `funcommands` | 官方插件(`plugins/`) | 上游 SourceMod |
| `funvotes` | 官方插件(`plugins/`) | 上游 SourceMod |
| `mapchooser` | 官方插件(`plugins/disabled/`,默认停用);`advertisements` 对它的依赖已降为软依赖 | 上游 SourceMod |
| `nominations` | 官方插件(`plugins/disabled/`) | 上游 SourceMod |
| `playercommands` | 官方插件(`plugins/`) | 上游 SourceMod |
| `reservedslots` | 官方插件(`plugins/`) | 上游 SourceMod |
| `rockthevote` | 官方插件(`plugins/disabled/`) | 上游 SourceMod |
| `sounds` | 官方插件(`plugins/`) | 上游 SourceMod |
| `sql-admin-manager` | 官方插件(`plugins/disabled/`) | 上游 SourceMod |

另外三个第三方插件(都没有源码,且当前不使用)曾作为「停用副本」放在
`bms/addons/sourcemod/plugins/disabled/` 里,**现已从仓库移除**:`classicmovement`(经典移动)、
`sm_realbhop`(真 bhop)、`xms`(hl2dm 的比赛插件,曾是 `bms_match` 的参考实现)。
`disabled/` 现在只剩 `spawn_marker.smx`。

> **SourceBans++ 已移除(2026-10-04)**:`sbpp_*` 六个模块连同 `configs/sourcebans/` 和 `sourcebanspp.inc`
> / `sourcecomms.inc` 一起从仓库删除,`BMAG.smx` 已重编译(41 → 35 个模块)。
> **因此 BMAG 现在不再提供任何封禁命令**
> (`sm_ban` / `sm_addban` / `sm_unban` / `sm_banip` 全部消失);**禁言禁麦不受影响** ——
> 它由官方插件 `basecomm` 提供,而 `basecomm` 现在由用户自己的 SourceMod 安装加载,BMAG 不再参与。
> 当时 `basevotes` 的 `sm_voteban` 也还在,但**已在第二批清理中随 `basevotes` 一起移出 BMAG**,
> 所以 BMAG 自己不提供投票封禁(装官方 `basevotes.smx` 即可,默认就是启用的)。
> 顺带更正一处旧描述:**被移出前的 `basevotes/voteban.sp` 与上游逐字节一致**,
> 它投票通过后只执行 `ServerCommand("kickid ...")`(踢人),**本来就不写封禁名单**
> —— 早先 README 里"已改走 SourceMod 核心的本地封禁"的说法不成立。
> (该源码现已删除,结论出自删除前的比对。)
> 要真正的封禁功能,装 SourceBans++(第三方)或启用官方 `basebans.smx`
> (它在官方包里默认启用,但本仓库 `plugins/disabled/basebans.smx` 那份副本已删除)。

---

## 五、从源码构建

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

### SDK 版本与升级记录

**当前固定的是 SourceMod 官方最新稳定版 `1.12.0.7255`**(2026-10-02,即
[`alliedmodders/sourcemod` 的 `releases/latest`](https://github.com/alliedmodders/sourcemod/releases) ——
`1.13.0-git7475` 是更快的开发线但标为 prerelease,没有采用)。
`smx_analysis/dl/` 里只留了 `spcomp.exe`(1.1 MB)—— 官方包其余内容(`bin/`、`extensions/`、
`translations/`、官方插件源码)对构建没用,已不再入库;`src/scripting/include/` 就是官方 1.12 的原样 include。

**从 1.11.0.6608 升上来时,1.12 的编译器收紧了两处检查,顺带暴露了两个一直藏在源码里的问题**(都已修好):

| 位置 | 1.11 的表现 | 1.12 的表现 | 修法 |
|---|---|---|---|
| `textmsg_fix.sp` → `SafePrintHintTextAll()` | 静默容忍(该函数是死代码,从没被调用过) | `error 017: undefined symbol "PrintHintTextAll"` | 改成 SDK 里的正确名字 `PrintHintTextToAll` |
| `advertisements.sp` → `Timer_DisplayAd()` | 仅 `warning 209: function should return a value` | `error 078: function uses both "return" and "return <value>"` | 裸 `return;` 改成 `return Plugin_Continue;` |

> ⚠️ **升级 SDK 会抬高服务器端的最低版本。** 用 1.12 的 include 编出来的 `BMAG.smx` 可能引用
> 1.11 没有的 native —— **部署前请把服务器上的 SourceMod 也升到 1.12**,否则 BMAG 会加载失败。
> 「编译用的 `include/` 必须与生产服务器一致」这条从建议变成了硬要求。

> **构建产物落在 `smx_analysis/src/scripting/BMAG/BMAG.smx`,该目录整体是 gitignore 的。**
> 要让本地 `bms/` 部署树保持可用,把那一步产物拷过去:
>
> ```bat
> copy /Y smx_analysis\src\scripting\BMAG\BMAG.smx  bms\addons\sourcemod\plugins\
> ```
>
> 两份**都不入库**(见[目录结构](#目录结构)的说明)。仓库里再也不同时存两份同名 `BMAG.smx`,
> 也就没有「两处必须一致」的手工约定了 —— 代价是全新克隆后得先构建(或解压 CI artifact)才有成品。
> CI(`.github/workflows/build.yml`)只产出构建输出那一份;部署树里的那份要手动同步。

### CI(`.github/workflows/build.yml`)

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

---

## 六、已知问题

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
