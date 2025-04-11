#include "read_mcp3008.h"
#include <SPI.h>

// MCP3008 の CS ピン（必要に応じて変更）
static const int CS_PIN = 17;

int readMCP3008(int channel) {
    if (channel < 0 || channel > 7) {
        return -1; // チャンネル範囲外
    }

    // SPIトランザクション設定：1MHz、MSB First、MODE0
    // 必要に応じて速度などを調整
    SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));

    digitalWrite(CS_PIN, LOW); // MCP3008 と通信開始

    // 1バイト目：スタートビット (0b00000001)
    SPI.transfer(0x01);

    // 2バイト目：シングルエンド + チャンネル指定 (0b1000xxxx)
    byte command = 0b10000000 | (channel << 4);
    byte highByte = SPI.transfer(command);

    // 3バイト目：受信データ
    byte lowByte = SPI.transfer(0x00);

    // 通信終了
    digitalWrite(CS_PIN, HIGH);
    SPI.endTransaction();

    // 10-bit のADC値を合成
    // highByte の下位2ビット + lowByte 全ビット
    int result = ((highByte & 0x03) << 8) | lowByte;
    return result;
}
