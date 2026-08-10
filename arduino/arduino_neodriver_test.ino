#include <Wire.h>
#include <seesaw_neopixel.h>

#define BOARD_ADDRESS 0x60
#define NUM_PIXELS 6
#define WAIT 5000

#define PIN 15

seesaw_NeoPixel strip = seesaw_NeoPixel(NUM_PIXELS, PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  Serial.begin(115200);
  Wire.begin();
  while (!Serial) delay(10);

  Serial.println("");
  Serial.println("");
  Serial.println("");
  Serial.println("------------- BEGIN ARDUINO-NEOPIXEL TESTS -------------");
  Serial.printf("Set board address: 0x%X\r\n", BOARD_ADDRESS);

  // I2C DEVICE SCAN
  Serial.println("");
  Serial.println("------ I2C DEVICE SCAN ------");

  I2C_Scan();

  // NEODRIVER SETUP TEST
  Serial.println("");
  Serial.println("------ NEODRIVER SETUP TEST ------");

  if (!strip.begin(BOARD_ADDRESS)) {
    Serial.printf("NeoDriver not found at 0x%X!\r\n", BOARD_ADDRESS);
    while (1) delay(10);
  }

  Serial.printf("NeoDriver at 0x%X was found\r\n", BOARD_ADDRESS);

  strip.show();
}

void loop() {
  Serial.println("");
  Serial.println("Starting LED pixel tests...");
  delay(WAIT);

  // OFF TEST
  Serial.println("");
  Serial.println("------ OFF TEST ------");

  Serial.printf("All LED pixels should be OFF for %d ms\r\n", WAIT);
  delay(WAIT);

  // RGB TESTS
  Serial.println("");
  Serial.println("------ RGB TESTS ------");

  setColour(255,0,0);
  Serial.printf("All %d pixels should be RED for %d ms\r\n", NUM_PIXELS, WAIT);
  delay(WAIT);
  
  setColour(0,255,0);
  Serial.printf("All %d pixels should be GREEN for %d ms\r\n", NUM_PIXELS, WAIT);
  delay(WAIT);
  
  setColour(0,0,255);
  Serial.printf("All %d pixels should be BLUE for %d ms\r\n", NUM_PIXELS, WAIT);
  delay(WAIT);

  setColour(255,255,255);
  Serial.printf("All %d pixels should be WHITE for %d ms\r\n", NUM_PIXELS, WAIT);
  delay(WAIT);

  // BRIGHTNESS TESTS
  Serial.println("");
  Serial.println("------ BRIGHTNESS TESTS ------");

  setBrightness(20,255,255,255);
  Serial.printf("All %d pixels should be dimmer for %d ms\r\n", NUM_PIXELS, WAIT);
  delay(WAIT);

  setBrightness(1,255,255,255);
  Serial.printf("All LED pixels should be OFF for %d ms\r\n", WAIT);
  delay(WAIT);

  setBrightness(255,255,255,255);
  Serial.printf("All %d pixels should be bright for %d ms\r\n", NUM_PIXELS, WAIT);
  delay(WAIT);

  // LENGTH TESTS
  Serial.println("");
  Serial.println("------ LENGTH TESTS ------");

  uint16_t length = 1;

  setColour(0,0,0);
  setLength(length);
  setColour(255,255,255);
  Serial.printf("Only %d pixel should be ON for %d ms\r\n", length, WAIT);
  delay(WAIT);

  length = 5;
  setColour(0,0,0);
  setLength(length);
  setColour(255,255,255);
  Serial.printf("Only the first %d pixels should be ON for %d ms\r\n", length, WAIT);
  delay(WAIT);

  length = 1;
  setLength(length);
  setColour(255,0,0);
  Serial.printf("The first pixel should turn RED for %d ms\r\n", length, WAIT);
  delay(WAIT);

  length = NUM_PIXELS;
  setColour(0,0,0);
  setLength(length);
  setColour(0,255,0);
  Serial.printf("All %d pixels should be GREEN for %d ms\r\n", length, WAIT);
  delay(WAIT);

  // Tests done
  Serial.println("");
  Serial.println("All tests done :) Turning off LED pixels...");
  setColour(0,0,0);
  while(true) {}
}

void I2C_Scan() {
  byte error, address;
  int nDevices = 0;

  for (address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("I2C device found at address 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
      nDevices++;
    }
  }

  if (nDevices == 0) Serial.println("No I2C devices found");
}

void setColour(uint8_t r, uint8_t g, uint8_t b) {
  for (uint16_t i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
}

void setBrightness(uint8_t val, uint8_t r, uint8_t g, uint8_t b) {
  strip.setBrightness(val);
  setColour(r,g,b);
}

void setLength(uint16_t n) {
  strip.updateLength(n);
}