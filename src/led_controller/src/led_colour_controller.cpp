#include <chrono>
#include <cstdlib>

#include <rclcpp>
#include <rclcpp_lifecycle/lifecycle_node.hpp>
#include <led_controller/msg/rgb.hpp>

using namespace std::chrono_literals;

typedef rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn LifecycleCallback;

class LedColourControllerNode : public rclcpp_lifecycle::LifecycleNode {
    public:
        explicit LedColourControllerNode(const std::string &name) : rclcpp_lifecycle::LifecycleNode(name) {}

        LifecycleCallback on_configure(const rclcpp_lifecycle::State &) {
            RCLCPP_INFO(this->get_logger(), "Configuring LED Colour Controller");

            pub_ = this->create_publisher<led_controller::msg::RGB>("led_colour", 10);
            timer_ = this->create_wall_timer(1s, std::bind(&LedColourControllerNode::publish_random_colour, this));

            publish_colour(255, 255, 0); // Turn to yellow after configuring

            return LifecycleCallback::Success;
        }

        LifecycleCallback on_activate(const rclcpp_lifecycle::State &state) {
            RCLCPP_INFO(this->get_logger(), "Activating LED Colour Controller");

            LifecycleNode::on_activate(state);

            return LifecycleCallback::Success;
        }

        LifecycleCallback on_deactivate(const rclcpp_lifecycle::State &state) {
            RCLCPP_INFO(this->get_logger(), "Deactivating LED Colour Controller");

            LifecycleNode::on_deactivate(state);

            publish_colour(255, 0, 0); // Turn to red on deactivate

            return LifecycleCallback::Success;
        }

        LifecycleCallback on_cleanup(const rclcpp_lifecycle::State &state) {
            RCLCPP_INFO(this->get_logger(), "Cleaning up LED Colour Controller");

            timer_.reset();
            pub_.reset();

            return LifecycleCallback::Success;
        }

        LifecycleCallback on_shutdown(const rclcpp_lifecycle::State &state) {
            RCLCPP_INFO(this->get_logger(), "Shuting down LED Colour Controller");

            timer_.reset();
            pub_.reset();

            return LifecycleCallback::Success;
        }

    private:
        void publish_colour(std::uint8_t r, std::uint8_t g, std::uint8_t b) {
            auto colour = std::make_unique<led_controller::msg::RGB>();
            colour->red_val = r;
            colour->green_val = g;
            colour->blue_val = b;

            RCLCPP_INFO("Publishing colour: R(%d), G(%d), B(%d)", colour->red_val, colour->green_val, colour->blue_val);
            pub_->publish(std::move(colour));
        };
        void publish_random_colour() {
            publish_colour(rand() % 256, rand() % 256, rand() % 256);
        };

        // Using regular publisher to allow colour changing in inactive state
        std::shared_ptr<rclcpp::Publisher<led_controller::msg::RGB>> pub_;
        std::shared_ptr<rclcpp::TimerBase> timer_;
}