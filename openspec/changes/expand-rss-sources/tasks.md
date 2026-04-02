## 1. 外部 RSS 支持

- [x] 1.1 修改 rss_spider.py — RSSSpider.__init__ 判断 config.url 存在时直接用作 feed_url
- [x] 1.2 修改 collector.py — create_spider() 增加 type == "rss" 分支，创建 RSSSpider

## 2. 验证 RSSHub 路由可用性

- [x] 2.1 逐一验证候选 RSSHub 路由 — 9 条可用：wallstreetcn、jandan、guokr、bbc-chinese、kr-news、huxiu、readhub、cnbeta、solidot
- [x] 2.2 验证候选外部 RSS 链接 — 3 条可用：ruanyifeng、solidot-rss、infoq-cn

## 3. 新增源配置

- [x] 3.1 在 sources.yaml 中添加 8 个 RSSHub 源（wallstreetcn、bbc-chinese、readhub、huxiu、cnbeta、solidot、guokr、jandan）
- [x] 3.2 在 sources.yaml 中添加 2 个外部 RSS 源（ruanyifeng、infoq-cn）

## 4. 前端同步

- [x] 4.1 在 BriefingsView.vue 的 sourceOptions 数组中添加 10 个新源

## 5. 部署验证

- [x] 5.1 Docker 构建部署 app + frontend — 两个容器均已重建
- [x] 5.2 E2E 验证 — 8 个 RSSHub 源全部采集成功（共 169 条），infoq-cn 采集 20 条，ruanyifeng 待整点触发（cron 0 * * * *）
