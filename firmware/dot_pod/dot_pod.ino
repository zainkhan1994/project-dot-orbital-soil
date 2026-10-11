/*
 * Project D.O.T. pod firmware (Arduino Uno/Mega class)
 *
 * Reads soil moisture, soil pH, air temperature/humidity and NPK, then prints one JSON
 * object per line over USB serial every SAMPLE_MS. bridge/serial_bridge.py forwards those
 * lines to the backend (POST /api/ingest).
 *
 * Wiring (adjust to your build):
 *   DHT22 data ........ D2          (Adafruit "DHT sensor library" + "Adafruit Unified Sensor")
 *   Soil moisture ..... A0          (capacitive sensor, analog)
 *   Soil pH ........... A1          (analog pH probe board)
 *   RS485 module ...... RX D10, TX D11, DE/RE D8   (NPK probe, Modbus RTU, 4800 baud)
 *
 * NOTE: this sketch has not been compiled or run on hardware in this repository's CI.
 * The calibration constants below are placeholders: calibrate each probe against known
 * references before trusting the numbers.
 */
#include <DHT.h>
#include <SoftwareSerial.h>

#define DHT_PIN 2
#define DHT_TYPE DHT22
#define MOISTURE_PIN A0
#define PH_PIN A1
#define RS485_RX 10
#define RS485_TX 11
#define RS485_DE_RE 8

const unsigned long SAMPLE_MS = 2000;

// Capacitive moisture: raw ADC in air (dry) and fully submerged (wet). Measure yours.
const int MOISTURE_DRY = 620;
const int MOISTURE_WET = 310;

// Two-point pH calibration: raw ADC at pH 4.01 and pH 6.86 buffer solutions. Measure yours.
const float PH_RAW_A = 560.0, PH_VAL_A = 4.01;
const float PH_RAW_B = 470.0, PH_VAL_B = 6.86;

DHT dht(DHT_PIN, DHT_TYPE);
SoftwareSerial rs485(RS485_RX, RS485_TX);

// Modbus RTU request: address 0x01, function 0x03, start register 0x001E, 3 registers (N, P, K).
// This register map is the one used by common low-cost RS485 NPK probes; check your datasheet.
const byte NPK_REQUEST[] = {0x01, 0x03, 0x00, 0x1E, 0x00, 0x03, 0x65, 0xCD};

bool readNPK(int &n, int &p, int &k) {
  byte resp[11];
  digitalWrite(RS485_DE_RE, HIGH);            // transmit
  delay(2);
  rs485.write(NPK_REQUEST, sizeof(NPK_REQUEST));
  rs485.flush();
  digitalWrite(RS485_DE_RE, LOW);             // receive
  unsigned long start = millis();
  byte got = 0;
  while (got < sizeof(resp) && millis() - start < 300) {
    if (rs485.available()) resp[got++] = rs485.read();
  }
  if (got < sizeof(resp) || resp[0] != 0x01 || resp[1] != 0x03 || resp[2] != 0x06) return false;
  n = (resp[3] << 8) | resp[4];
  p = (resp[5] << 8) | resp[6];
  k = (resp[7] << 8) | resp[8];
  return true;
}

float moisturePercent() {
  int raw = analogRead(MOISTURE_PIN);
  float pct = 100.0 * (MOISTURE_DRY - raw) / (float)(MOISTURE_DRY - MOISTURE_WET);
  return constrain(pct, 0.0, 100.0);
}

float phValue() {
  long sum = 0;
  for (int i = 0; i < 10; i++) { sum += analogRead(PH_PIN); delay(5); }
  float raw = sum / 10.0;
  float slope = (PH_VAL_B - PH_VAL_A) / (PH_RAW_B - PH_RAW_A);
  return PH_VAL_A + slope * (raw - PH_RAW_A);
}

void setup() {
  Serial.begin(115200);
  rs485.begin(4800);
  pinMode(RS485_DE_RE, OUTPUT);
  digitalWrite(RS485_DE_RE, LOW);
  dht.begin();
}

void loop() {
  static unsigned long last = 0;
  if (millis() - last < SAMPLE_MS) return;
  last = millis();

  float t = dht.readTemperature();
  float h = dht.readHumidity();
  int n = 0, p = 0, k = 0;
  bool npkOk = readNPK(n, p, k);
  if (isnan(t) || isnan(h) || !npkOk) {
    Serial.println("{\"error\":\"sensor read failed\"}");
    return;
  }
  Serial.print("{\"nitrogen\":");   Serial.print(n);
  Serial.print(",\"phosphorus\":"); Serial.print(p);
  Serial.print(",\"potassium\":");  Serial.print(k);
  Serial.print(",\"moisture\":");   Serial.print(moisturePercent(), 1);
  Serial.print(",\"ph\":");         Serial.print(phValue(), 2);
  Serial.print(",\"temperature\":"); Serial.print(t, 1);
  Serial.print(",\"humidity\":");   Serial.print(h, 1);
  Serial.println("}");
}
