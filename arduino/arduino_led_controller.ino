#include <seesaw_neopixel.h>

// NEODRIVER
#define BOARD_ADDRESS 0x60
#define NUM_PIXELS 5
#define PIN 15

#define MIN_PIXELS 0

// UART
#define MAX_LINE_READS 5

// PWM
#define PWM_TIMEOUT 500 // in ms
#define PWM_TIMEOUT_DUTY 0
#define PWM_FREQ 50 // in Hz
#define PWM_RES 12 // bits
#define PWM_CHANNEL 0
const int PWM_PIN = A6;

int pwm_timeout = PWM_TIMEOUT;
int pwm_prev_count = 0;
bool pwm_active = false;

// DEBUG
const bool PWM_DEBUG = true;

// Arduino Code
seesaw_NeoPixel strip = seesaw_NeoPixel(NUM_PIXELS, PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  Serial.begin(115200);
  
  while (!Serial) delay(10);   // wait until serial port is opened
  
  if (!PWM_DEBUG) {
    if(!strip.begin(BOARD_ADDRESS)){
      Serial.println("seesaw not found!");
      while(1) delay(10);
    }
    
    Serial.println(F("seesaw started OK!"));
    
    strip.show(); // Initialize all pixels to 'off'
  } else {
    Serial.println("In PWM_DEBUG mode");
  }
  
  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RES);
  ledcAttachPin(PWM_PIN, PWM_CHANNEL);
}

void loop() {
  checkPWMTimeout();
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

  // LED
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
  // PWM
  else if (functionID == "pd") {
    const uint8_t args = 2;
    int payload[args];

    if (!parseProtocol(line, payload, args)) { return; }
    setPWMDutyCyclePercent(payload[0], payload[1]);
  }
  else if (functionID == "pf") {
    const uint8_t args = 1;
    int payload[args];

    if (!parseProtocol(line, payload, args)) { return; }
    setPWMFrequency(payload[0]);
  }
  else if (functionID == "pt") {
    const uint8_t args = 1;
    int payload[args];

    if (!parseProtocol(line, payload, args)) { return; }
    setPWMTimeout(payload[0]);
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

void setColour(int r_arg, int g_arg, int b_arg) {
  uint8_t r = (uint8_t)constrain(r_arg, 0, 255);
  uint8_t g = (uint8_t)constrain(g_arg, 0, 255);
  uint8_t b = (uint8_t)constrain(b_arg, 0, 255);

  for (uint16_t i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
  Serial.printf("setColour: To R(%d) G(%d) B(%d)\r\n", r, g, b);
}

void setBrightness(int b_arg) {
  uint8_t b = (uint8_t)constrain(b_arg, 0, 255);

  strip.setBrightness(b);
  strip.show();
  Serial.printf("setBrightness: To %d\r\n", b);
}

void setLength(int n_arg) {
  uint16_t n = (uint16_t)constrain(n_arg, MIN_PIXELS, UINT16_MAX);

  strip.updateLength(n);
  Serial.printf("setLength: To %d\r\n", n);
}

// PWM API

void checkPWMTimeout() {
  if (!pwm_active) return;

  int pwm_curr_count = millis();
  if (pwm_curr_count - pwm_prev_count >= pwm_timeout) {
    pwm_active = false;
    ledcWrite(PWM_CHANNEL, PWM_TIMEOUT_DUTY);
    Serial.printf("checkPWMTimeout: PWM timout reached\r\n");
  }
}

void resetPWMTimout() {
  pwm_prev_count = millis();
  Serial.printf("resetPWMTimout: PWM timeout reset\r\n");
}

void setPWMTimeout(int timeout) {
  pwm_timeout = timeout;
  Serial.printf("setPWMTimeout: PWM timeout changed to %d ms\r\n", timeout);
}

void setPWMDutyCyclePercent(int percent, int decimal) {
  percent = constrain(percent, 0, 100);
  decimal = percent == 100 ? 0 : decimal;
  decimal = max(0, decimal);

  float full_percent = percent + (float)decimal / pow(10.0, String(decimal).length());
  uint32_t value = (uint32_t)round((full_percent / 100.0) * pow(2, PWM_RES));

  resetPWMTimout();

  ledcWrite(PWM_CHANNEL, value);
  Serial.printf("setDutyCycle: Duty cycle set to ~%d percent (%d/4095) \r\n", percent, value);

  pwm_active = true;
}

void setPWMFrequency(int f_arg) {
  uint32_t f = (uint32_t)constrain(f_arg, 0, UINT32_MAX);

  ledcChangeFrequency(PWM_CHANNEL, f, PWM_RES);
  Serial.printf("setPWMFrequency: To %d Hz\r\n", f);
}