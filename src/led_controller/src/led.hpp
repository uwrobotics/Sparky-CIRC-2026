#ifndef LED_HPP
#define LED_HPP

#include <cstdlib>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/color_rgba.hpp"

enum class LEDColours
{
  RED,
  ORANGE,
  YELLOW,
  GREEN,
  BLUE,
  PURPLE,
  WHITE
};

class LED
{
public:
  LED(std::shared_ptr<rclcpp::Publisher<std_msgs::msg::ColorRGBA>> pub_, rclcpp::Logger logger);
  void set_colour(float r, float g, float b, float a = 0);
  void set_colour(LEDColours colour_name);
  void set_random_colour();

private:
  std::shared_ptr<rclcpp::Publisher<std_msgs::msg::ColorRGBA>> pub_;
  rclcpp::Logger logger;
  std::unique_ptr<std_msgs::msg::ColorRGBA> curr_colour_;
};

#endif
