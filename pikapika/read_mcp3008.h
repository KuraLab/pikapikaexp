#pragma once
#include <Arduino.h>

/**
 * @brief MCP3008 の指定したチャンネルから 10-bit のアナログ値を取得する
 * 
 * @param channel 読み取りたいチャンネル番号 (0～7)
 * @return int MCP3008 から取得した 0～1023 の値
 */
int readMCP3008(int channel);
