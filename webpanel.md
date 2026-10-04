### 网页面板走反代部署(IIS / nginx)

面板本身是个**裸 HTTP 服务**(`http://{SERVER_IP_ADDR}:28015`)。在国内机房,这种"无备案域名的公网 HTTP"
容易被阻断,而且它会把面板、`/status` 和明文 token 直接暴露到公网。

**推荐做法:让面板只监听回环,由你已备案的站点(HTTPS)反代过去。**

插件侧只需要两个 cvar:

```cfg
sm_bms_webpanel_bind "127.0.0.1"                    // 默认值,别改;面板不再对外监听
sm_bms_webpanel_port "28015"                        // 内部监听端口,可按需改(改完即时重绑)
sm_bms_webpanel_url  "https://panel.example.com"    // 玩家浏览器看到的地址(备案域名)
```

`sm_bms_webpanel_url` 会同时用于页面里的 `__BASE__` 和 `!panel` 打开的 MOTD 地址 ——
设了它,对内是 `http://<bind>:<port>`,对外是 HTTPS 域名,两边各司其职。
内部端口随便改(比如和别的服务撞了):反代那边把 `proxy_pass` / `Rewrite` 的目标端口同步改掉即可,
**对外的 URL 不受影响**。

#### IIS(ARR + URL Rewrite)

前置:装 **Application Request Routing** 与 **URL Rewrite**,并在
*IIS 管理器 → 服务器节点 → Application Request Routing Cache → Server Proxy Settings*
里勾上 **Enable proxy**。

站点的 `web.config`(整站反代到面板,用子域名最省事):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="BMAG panel" stopProcessing="true">
          <match url="(.*)" />
          <action type="Rewrite" url="http://127.0.0.1:28015/{R:1}" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
```

想挂在**子路径**(如 `https://site.example.com/bms/`)也行,规则里把前缀剥掉即可:

```xml
<rule name="BMAG panel under /bms" stopProcessing="true">
  <match url="^bms/(.*)" />
  <action type="Rewrite" url="http://127.0.0.1:28015/{R:1}" />
</rule>
```

对应的 `sm_bms_webpanel_url` 写 `https://site.example.com/bms`(基址不带结尾斜杠也可,插件会自己去掉)。

#### nginx

```nginx
location / {
    proxy_pass http://127.0.0.1:28015;   # 结尾不加斜杠 → 路径原样透传
    proxy_set_header Host $host;
    proxy_read_timeout 5s;
}
```

#### 反代之后顺手能做的事

| 想做的事 | 怎么做 |
|---|---|
| 挡掉无鉴权的 `/status` | IIS:给 `/status` 加一条 `<action type="CustomResponse" statusCode="403" />` 的规则;nginx:`location = /status { deny all; }` |
| 限流(token 端点防刷) | nginx `limit_req`;IIS 用 Dynamic IP Restrictions |
| TLS | 用你已备案域名签发的证书终结在反代上,插件侧永远是明文回环 |

> **前置条件:反代进程必须能访问游戏服的 `127.0.0.1:28015`** —— 也就是**同一台机器**。
> 如果反代在别的机器上,先架隧道(WireGuard / `ssh -L` / frp),再把 `sm_bms_webpanel_bind`
> 指到隧道在本机的地址(而不是 `0.0.0.0`,别把面板重新暴露出去)。
