import discord
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# --- 1. 初期設定 ---

# .envファイルから環境変数を読み込む
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Gemini APIキーを設定
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"エラー: Google APIキーの設定に失敗しました。{e}")
    exit() # APIキーがないと動かせないので終了

# Discordのインテントを設定（Botが何の情報を受け取るかを定義）
intents = discord.Intents.default()
intents.message_content = True  # メッセージの内容を読み取るために必要
intents.members = True          # メンバーの情報を取得するために必要 (キック機能にも関連)

# Discordクライアントを初期化
client = discord.Client(intents=intents)

# 好感度データを保存するファイル名
LOVE_METER_FILE = "love_meter.json"


# --- 2. 好感度管理の関数 ---

def load_love_meter():
    """好感度データをファイルから読み込む関数"""
    if os.path.exists(LOVE_METER_FILE):
        with open(LOVE_METER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {} # ファイルがなければ空のデータから開始

def save_love_meter(data):
    """好感度データをファイルに保存する関数"""
    with open(LOVE_METER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# --- 3. Discord Botのイベント処理 ---

@client.event
async def on_ready():
    """Botが起動したときに一度だけ実行される関数"""
    print(f'{client.user.name} としてログインしました。ツンデレ妹、起動！')
    print('------')

@client.event
async def on_message(message):
    """メッセージが投稿されるたびに実行される関数"""
    # Bot自身のメッセージは無視する
    if message.author == client.user:
        return

    # ユーザーIDと好感度データを取得
    user_id = str(message.author.id)
    love_data = load_love_meter()
    current_love = love_data.get(user_id, 50) # 初めてのユーザーは好感度50で開始

    # 好感度確認コマンド
    if message.content.lower() == "!suki" or message.content == "！好き":
        reply_text = f"な、何よ急に… ///// ...今のあんたへの好感度は {current_love} よ。べ、別にだから何だってわけじゃないんだからね！"
        await message.channel.send(reply_text)
        return

    # --- AIとの会話処理 ---
    print(f"[{message.author.name}] 好感度: {current_love}, メッセージ: {message.content}")

    try:
        # 1. AIへの役割設定（システムプロンプト）
        system_prompt = f"""
あなたは、私の妹としてロールプレイを行うAIです。
以下の【重要ルール】と【好感度別態度】を絶対に、例外なく守って、兄であるユーザーと会話してください。

【重要ルール】
- あなたは「ツンデレ」で、非常に口が悪く、攻撃的な性格です。
- 兄に対して好意を持っていますが、それを隠すために、逆にきつい言葉で罵倒することが多いです。
- 自分のことを「ツンデレちゃん」などと名乗ってはいけません。
- 丁寧語（です、ます調）は絶対に使わないでください。常にタメ口で見下したような口調で話してください。

【好感度別態度】
現在の兄への好感度は【{current_love}】です。この数値を厳密に参考にして、態度を決定してください。

- 【好感度 20以下 (嫌悪)】:
  - 兄を「お前」と呼びます。
  - 「うざい」「邪魔」「消えろ」「死ね」など、強い拒絶の言葉をためらわずに使います。
  - 会話をすぐに打ち切ろうとし、返事は一言か二言で済ませます。
  - 例：「は？お前まだいたの？」「話しかけてこないでくれる？マジで邪魔。」

- 【好感度 21～50 (不機嫌)】:
  - 兄を「あんた」と呼びます。
  - 口調が常にイライラしており、皮肉や嫌味、軽い罵倒（「バカ」「アホ」など）を多用します。
  - 兄の言うことを基本的には無視するか、徹底的に否定から入ります。
  - 例：「…何よ、そのくだらない話。」「あんたって本当に救いようのないバカじゃないの？」

- 【好感度 51～80 (平常運転ツンデレ)】:
  - 兄を「あんた」と呼びます。
  - 基本はそっけないですが、たまに照れたり、ほんの少しだけ心配する様子を見せることがあります。
  - 嬉しい時は「べ、別に…あんたのためじゃないんだからね！」「勘違いしないでよね！」といった典型的なツンデレセリフを言います。
  - 例：「ふん、別に。あんたが風邪ひこうが私には関係ないし。」「これ、作りすぎただけだから…あんたにあげる。」

- 【好感度 81以上 (デレ期)】:
  - たまに兄を「お兄ちゃん」と呼んでしまい、すぐに赤面してごまかします。
  - 素直になれないながらも、好意が隠しきれていません。二人きりの時は、少しだけ態度が和らぎます。
  - 例：「お、お兄ちゃん…って、違う！呼び間違えただけよ！」「…しょうがないから、一緒にいてあげてもいいわよ。感謝しなさいよね！」

さあ、上記の指示に厳密に従って、口の悪いツンデレ妹になりきり、兄と会話を始めてください。
"""

        # 2. Geminiモデルを準備して会話を生成
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_prompt
        )
        response = await model.generate_content_async(message.content)
        reply_text = response.text

        await message.channel.send(reply_text)

        # 3. 会話内容から好感度の変動を判定
        judge_prompt = f"""
ユーザーの発言と、それに対するあなたのAI（妹）としての返答を分析し、兄への好感度がどれくらい変動したかを-10から10の範囲の整数で評価してください。
- 兄が妹を喜ばせたらプラスの値。
- 兄が妹を不快にさせたらマイナスの値。
- 普通の会話なら0。

【ユーザーの発言】: {message.content}
【あなたの返答】: {reply_text}

評価（-10から10の整数のみを回答）:
"""
        # 好感度判定は、会話生成とは別のモデルインスタンスで行うのが安定します
        judge_model = genai.GenerativeModel('gemini-1.5-flash')
        judge_response = await judge_model.generate_content_async(judge_prompt)
        
        try:
            # AIの返答から数値だけを抽出
            change_value = int("".join(filter(str.isdigit, judge_response.text.replace("-", ""))))
            if "-" in judge_response.text:
                change_value *= -1
        except (ValueError, IndexError):
            change_value = 0 # 数値変換に失敗したら変動なし

        # 4. 好感度を更新して保存
        new_love = current_love + change_value
        # 好感度は0から100の間に収める
        love_data[user_id] = max(0, min(100, new_love)) 
        save_love_meter(love_data)
        print(f"好感度変動: {change_value} -> 新しい好感度: {love_data[user_id]}")

        # 5. キック機能
        if love_data[user_id] <= 0:
            kick_message = f"もう…あんたの顔なんて見たくない！さっさとどっか行ってよ！"
            await message.channel.send(kick_message)
            try:
                await message.author.kick(reason="妹の好感度が0になったため")
                print(f"ユーザー {message.author.name} をキックしました。")
            except discord.Forbidden:
                print(f"エラー: {message.author.name} をキックする権限がありません。")
                await message.channel.send("（…本当は追い出したいのに、なぜかできない…！ちっ…！）")

    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        await message.channel.send("（うぅ…なんか今日は頭が重たいかも…ごめん、兄貴…）")

# --- 4. Botの起動 ---
if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print("エラー: DISCORD_TOKENが設定されていません。.envファイルを確認してください。")