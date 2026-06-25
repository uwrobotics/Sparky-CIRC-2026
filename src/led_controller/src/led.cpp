#include "led.hpp"

LED::LED(std::shared_ptr<rclcpp::Publisher<std_msgs::msg::ColorRGBA>> pub_, rclcpp::Logger logger)
: pub_(pub_), logger(logger) {}

bool LED::set_colour(float r, float g, float b, float a)
{
  auto colour = std::make_unique<std_msgs::msg::ColorRGBA>();
  colour->r = r;
  colour->g = g;
  colour->b = b;
  colour->a = a;

  RCLCPP_INFO(
    logger, "Publishing colour: R(%f), G(%f), B(%f), a(%f)",
    colour->r,
    colour->g,
    colour->b,
    colour->a
  );

  pub_->publish(std::move(colour));

  return true;
}

bool LED::set_colour(LEDColours colour_name)
{
  switch (colour_name) {
    case LEDColours::RED:
      set_colour(255, 0, 0);
      break;
    case LEDColours::ORANGE:
      set_colour(255, 128, 0);
      break;
    case LEDColours::YELLOW:
      set_colour(255, 255, 0);
      break;
    case LEDColours::GREEN:
      set_colour(0, 255, 0);
      break;
    case LEDColours::BLUE:
      set_colour(0, 0, 255);
      break;
    case LEDColours::PURPLE:
      set_colour(128, 0, 255);
      break;
    case LEDColours::WHITE:
      set_colour(255, 255, 255);
      break;
    default:
      RCLCPP_INFO(logger, "The following LEDColours enum did not map to an existing colour value: %s");
      return false;
  }

  return true;
}

bool LED::set_random_colour()
{
  return set_colour(rand() % 256, rand() % 256, rand() % 256);
}
