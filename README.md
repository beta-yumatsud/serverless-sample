# serverless-sample
serverlessを使ってみてのサンプルなど、
Codepipelineを使ってのECSデプロイ周りのSlackへの通知をやってみる。

# serverless
* [serverless](https://serverless.com/)とは
  * Lambda、API Gatewayなどを簡単に構成してくれる
  * AWS、GCP、Azureなどに対応
* terraformでやればよくない？
  * 今回のpipelineの通知とかを簡単にやりたいとかは全然こっちもあり
  * 他の通知も含めてちゃんと使う！となったら、terraformに移行するとかやれば良さげ

# やってみたこと

## 準備
* インストール
```
$ npm install -g serverless

$ serverless -v        
1.42.2

$ sls -v       
1.42.2
```
* SlackのWebhook URLを[ここから](https://slack.com/services/new/incoming-webhook)取得

## sample
* サービス作成
```
$ sls create --template aws-python3 --path sample
```
* デプロイ
```
$ sls deploy -v 
```
* テスト実行
```
$ sls invoke -f hello
```
* 削除
```
$ sls remove -v
```

## Slack通知
* 通知の中身(コード)自体は [CodePipelineのステータスをSlackへ通知](https://qiita.com/ot-nemoto/items/91886f4a18c1b4e80a45) を使わせていただきましたmm
* サービス作成
```
$ sls create --template aws-python3 --path notification-slack
```
* デプロイ
```
$ sls deploy -v 
```
* 削除
```
$ sls remove -v
```

# 今回やらなかったこと
* Webhook URLをkmsに保存する
  * 今回は簡単にやるためにserverlessの環境変数に設定した
  * ただし本来はあまりよくないので、terraformに移行するタイミングでkmsを使うようにすればいいか

# 参考
* CloudWatch Event
  * [CodePipeline](https://docs.aws.amazon.com/ja_jp/AmazonCloudWatch/latest/events/EventTypes.html#codepipeline_event_type)
  * [CodeBuild](https://docs.aws.amazon.com/ja_jp/codebuild/latest/userguide/sample-build-notifications.html#sample-build-notifications-ref)
  * [ECS](https://docs.aws.amazon.com/ja_jp/AmazonECS/latest/developerguide/ecs_cwe_events.html)
* Slack
  * [Slackのメッセージの見栄えを良くする](https://tmg0525.hatenadiary.jp/entry/2017/10/15/120336)
  * [SlackのIncoming Webhooksを使い倒す](https://qiita.com/ik-fib/items/b4a502d173a22b3947a0)
