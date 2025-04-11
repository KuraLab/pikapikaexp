#include <Arduino.h>
#include <SPI.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <LittleFS.h>

// 自作ヘッダ
#include "read_mcp3008.h"
#include "agent_config.h"

// Wi-Fi接続設定
const char* ssid     = "Potato6";
const char* password = "50lanumtu6";

// UDP送信先設定
IPAddress serverIP(192, 168, 1, 43); // 送信先PCのIP
unsigned int serverPort = 5000;      // データ送信用ポート
unsigned int paramServerPort = 5001; // パラメータ要求用ポート

WiFiUDP udp;      // 計測データ送信用
WiFiUDP udpParam; // パラメータ要求用

int agent_id = 0; // 各Picoごとに異なるID

// 内部ADC（GPIO27,28）の光センサ用 変数
uint16_t sensorRaw28, sensorRaw27;
float sensorV28, sensorV27;
float sensorV;
float sensorV_old = 0.0f;
float dvdt;               // dv/dt

// バッテリー電圧（GPIO26）
uint16_t batteryRaw;
float batteryV;

// MCP3008 追加用 (CH0, CH7)
uint16_t adcRaw0, adcRaw7;
float adcV0, adcV7;

// フェーズ変数
float phi = 0.0f;
float phidot = 0.0f;
float omega = 3.14f * 5.95f; // 初期値（サーバから取得できたら上書きされる）
float kappa = 1.0f;

// タイマー管理用
unsigned long previousMicros = 0;
unsigned long ntpRefMicros = 0;
unsigned long ntpRefEpoch = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nProgram Start.");

  // ピン設定
  pinMode(10, OUTPUT);
  pinMode(22, OUTPUT);
  pinMode(2, OUTPUT);
  pinMode(15, OUTPUT);

  // 内部ADCで12-bit読み込み設定
  analogReadResolution(12);

  // Wi-Fi接続
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");

  // UDPソケット
  udp.begin(serverPort);   // 送信用（begin()は送信のみなら必須ではないが念のため）
  udpParam.begin(5002);    // パラメータ要求用（ローカルポート5002を使用）

  // agent_id 読み込み
  agent_id = readAgentIdFromFile();
  Serial.print("Loaded agent_id: ");
  Serial.println(agent_id);

  // サーバからパラメータ取得
  if (requestParameters(agent_id, udpParam, serverIP, paramServerPort, omega, kappa)) {
    Serial.println("Parameter update succeeded.");
  } else {
    Serial.println("Using default parameters.");
  }

  // SPI 初期化 (MCP3008用)
  SPI.begin();
  pinMode(17, OUTPUT);
  digitalWrite(17, HIGH); // CSピンをHIGHに
}

void loop() {
  // 時間計測
  unsigned long currentMicros = micros();
  float dt = (currentMicros - previousMicros) / 1000000.0f;
  previousMicros = currentMicros;

  // 内部ADC (GPIO28, 27) の読み取り
  sensorRaw28 = analogRead(28);
  sensorV28   = sensorRaw28 * 3.3f / (1 << 12); // 12-bit -> 0～4095
  sensorRaw27 = analogRead(27);
  sensorV27   = sensorRaw27 * 3.3f / (1 << 12);

  // MCP3008 の CH0, CH7 読み取り
  adcRaw0 = readMCP3008(0);  // 10-bit -> 0～1023
  adcV0   = adcRaw0 * 3.3f / (1 << 10);
  adcRaw7 = readMCP3008(7);
  adcV7   = adcRaw7 * 3.3f / (1 << 10);

  // 各光センサの値を合計
  sensorV = sensorV28 + sensorV27 + adcV0 + adcV7;

  // バッテリー電圧 (GPIO26)
  batteryRaw = analogRead(26);
  batteryV   = batteryRaw * 6.6f / (1 << 12);

  // dv/dt
  if (dt > 0.0f) {
    dvdt = (sensorV - sensorV_old) / dt;
  } else {
    dvdt = 0.0f;
  }
  sensorV_old = sensorV;

  // デジタル出力制御 (4本)
  bool state = (cos(phi) > 0.9f);
  digitalWrite(10, state ? HIGH : LOW);
  digitalWrite(22, state ? HIGH : LOW);
  digitalWrite(2,  state ? HIGH : LOW);
  digitalWrite(15, state ? HIGH : LOW);

  // フェーズ変化率 phidot 計算と phi 更新
  phidot = omega - kappa * cos(phi) * dvdt;
  phi += phidot * dt;
  
  // 送信時刻 (秒)
  double timestamp = micros() / 1000000.0;

  // UDP 送信用メッセージ作成
  char buf[150];
  snprintf(buf, sizeof(buf),
           "ID=%d,PHI=%f,TS=%f,V=%f,Vbat=%f,ADC0=%f,ADC7=%f",
           agent_id, phi, timestamp, sensorV, batteryV, adcV0, adcV7);

  // UDP 送信
  udp.beginPacket(serverIP, serverPort);
  udp.print(buf);
  udp.endPacket();

  delay(5);
}
