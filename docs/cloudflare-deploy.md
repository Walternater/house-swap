# Cloudflare Pages 部署指南（house-swap 看板）

> web/ 是纯静态前端（零后端、零网络调用、数据全在 localStorage），
> 用 Cloudflare Pages 免费托管，全球 CDN + 自动 HTTPS。

## 方式 A：GitHub 集成（推荐，push 即部署）

1. 建 GitHub 仓库并推送:
   ```bash
   cd /Users/wcf/personal/house-swap
   git remote add origin https://github.com/<你的账号>/house-swap.git
   git push -u origin main
   ```
2. Cloudflare 控制台 → Workers & Pages → Create → Pages → Connect to Git
3. 选 house-swap 仓库，构建配置:
   - 构建命令: 留空（纯静态无需构建）
   - 输出目录: `web`
4. 保存即部署 → 得到 `https://<project>.pages.dev`

## 方式 B：Wrangler 直传（不碰 GitHub）

```bash
npm install -g wrangler
cd /Users/wcf/personal/house-swap
wrangler login
wrangler pages deploy web/ --project-name house-swap
# → 部署到 https://house-swap.pages.dev
```
每次更新后重跑最后一条命令即可。

## 注意

- 看板政策硬编码在 web/app.js 的 POLICY 常量；改政策需改代码重新部署
- 数据只存浏览器 localStorage，换域名不影响（各域名独立存储）
- CI 已含测试（.github/workflows/ci.yml），GitHub 集成后 push 自动跑测试再部署
