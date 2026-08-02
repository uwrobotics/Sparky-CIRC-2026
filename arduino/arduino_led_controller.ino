#include <seesaw_neopixel.h>

#define BOARD_ADDRESS 0x60
#define NUM_PIXELS 5
#define PIN 15

#define MAX_LINE_READS 5
#define MIN_PIXELS 0

seesaw_NeoPixel strip = seesaw_NeoPixel(NUM_PIXELS, PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  Serial.begin(115200);
  
  while (!Serial) delay(10);   // wait until serial port is opened
  
  if(!strip.begin(BOARD_ADDRESS)){
    Serial.println("seesaw not found!");
    while(1) delay(10);
  }
  
  Serial.println(F("seesaw started OK!"));
  
  strip.show(); // Initialize all pixels to 'off'
}

void loop() {
  receiveUART();
}

// UART Communication

void receiveUART() {
  uint8_t lineCounter = 0;
  while(Serial.available() > 0 && lineCounter < MAX_LINE_READS) {
    String line = Serial.readStringUntil('\n');
    Serial.print("receieveUART: Received: ");
    Serial.println(line);

    decodeUART(line);

    lineCounter++;
  }
}

void decodeUART(String line) {
  String functionID = line.substring(0,2);

  if (functionID == "sc")
  {
    const uint8_t args = 3;
    int payload[args];

    if (!parseProtocol(line, payload, args)) { return; }
    setColour(payload[0], payload[1], payload[2]);
  }
  else if (functionID == "sb")
  {
    const uint8_t args = 1;
    int payload[args];

    if (!parseProtocol(line, payload, args)) { return; }
    setBrightness(payload[0]);
  }
  else if (functionID == "sl")
  {
    const uint8_t args = 1;
    int payload[args];

    if (!parseProtocol(line, payload, args)) { return; }
    setLength(payload[0]);
  }
  else
  {
    Serial.print("decodeUART: fid not recognized: ");
    Serial.println(functionID);
  }
}

bool parseProtocol(String line, int payload[], uint8_t args) {
  String currLine = line.substring(2);
  for (int i = 0; i < args; i++) {
    int separatorIndex = currLine.indexOf(",");

    if (separatorIndex == -1 && i != (args - 1)) {
      Serial.println("parseProtocol: Could not decode function arguments");
      return false;
    }

    String arg = currLine.substring(0, separatorIndex);
    if (!isOnlyDigits(arg)) {
      Serial.println("parseProtocol: Argument did not contain only digits");
      return false;
    }
    payload[i] = arg.toInt();

    currLine = currLine.substring(separatorIndex + 1);
  }
  return true;
}

bool isOnlyDigits(String string) {
  if (string.length() == 0) return false;

  uint8_t startIndex = 0;
  if (string.charAt(0) == '-') {
    if (string.length() == 1) return false;
    startIndex = 1;
  }

  for (int i = startIndex; i < string.length(); i++) {
    if (!isDigit(string.charAt(i))) return false;
  }
  return true;
}

// LED API

void setColour(int r, int g, int b) {
  r = (uint8_t)constrain(r, 0, 255);
  g = (uint8_t)constrain(g, 0, 255);
  b = (uint8_t)constrain(b, 0, 255);

  for (uint16_t i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
  Serial.printf("setColour: To R(%d) G(%d) B(%d)\r\n", r, g, b);
}

void setBrightness(int b) {
  b = (uint8_t)constrain(b, 0, 255);

  strip.setBrightness(b);
  strip.show();
  Serial.printf("setBrightness: To %d\r\n", b);
}

void setLength(int n) {
  n = (uint16_t)max(MIN_PIXELS,n);

  strip.updateLength(n);
  Serial.printf("setLength: To %d\r\n", n);
}