#include <chrono>
#include <memory>

#include "rclcpp_lifecycle/lifecycle_node.hpp"
#include "led.hpp"

using namespace std::chrono_literals;

using LifecycleCallback = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

class LedColourControllerNode : public rclcpp_lifecycle::LifecycleNode
{
    public:
        explicit LedColourControllerNode(const std::string &name) : rclcpp_lifecycle::LifecycleNode(name) {}

        LifecycleCallback on_configure(const rclcpp_lifecycle::State &)
        {
            RCLCPP_INFO(this->get_logger(), "Configuring LED Colour Controller");

            pub_ = this->create_publisher<std_msgs::msg::ColorRGBA>("led_colour", 10);

            led_ = std::make_shared<LED>(pub_, this->get_logger());

            timer_ = this->create_wall_timer(1s, std::bind(&LED::set_random_colour, led_.get()));
            timer_->cancel(); // Start with the timer stopped

            led_->set_colour(LEDColours::YELLOW);

            return LifecycleCallback::SUCCESS;
        }

        LifecycleCallback on_activate(const rclcpp_lifecycle::State& state)
        {
            RCLCPP_INFO(this->get_logger(), "Activating LED Colour Controller");

            LifecycleNode::on_activate(state);

            timer_->reset(); // Resume timer on activate

            return LifecycleCallback::SUCCESS;
        }

        LifecycleCallback on_deactivate(const rclcpp_lifecycle::State& state)
        {
            RCLCPP_INFO(this->get_logger(), "Deactivating LED Colour Controller");

            LifecycleNode::on_deactivate(state);

            timer_->cancel();

            led_->set_colour(LEDColours::RED);

            return LifecycleCallback::SUCCESS;
        }

        LifecycleCallback on_cleanup(const rclcpp_lifecycle::State& state)
        {
            RCLCPP_INFO(this->get_logger(), "Cleaning up LED Colour Controller");

            timer_.reset();
            pub_.reset();

            return LifecycleCallback::SUCCESS;
        }

        LifecycleCallback on_shutdown(const rclcpp_lifecycle::State& state)
        {
            RCLCPP_INFO(this->get_logger(), "Shuting down LED Colour Controller");

            timer_.reset();
            pub_.reset();

            return LifecycleCallback::SUCCESS;
        }

    private:
        // Using regular publisher to allow colour changing in inactive state
        std::shared_ptr<rclcpp::Publisher<std_msgs::msg::ColorRGBA>> pub_;
        std::shared_ptr<rclcpp::TimerBase> timer_;
        std::shared_ptr<LED> led_;
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);

    rclcpp::executors::SingleThreadedExecutor executor;
    auto node = std::make_shared<LedColourControllerNode>("led_colour_controller_node");

    executor.add_node(node->get_node_base_interface());
    executor.spin();

    rclcpp::shutdown();
    return 0;
}