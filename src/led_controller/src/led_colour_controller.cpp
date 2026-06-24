#include <chrono>
#include <cstdlib>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/lifecycle_node.hpp"
#include "std_msgs/msg/color_rgba.hpp"

using namespace std::chrono_literals;

using LifecycleCallback = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

class LedColourControllerNode : public rclcpp_lifecycle::LifecycleNode {
    public:
        explicit LedColourControllerNode(const std::string &name) : rclcpp_lifecycle::LifecycleNode(name) {}

        LifecycleCallback on_configure(const rclcpp_lifecycle::State &) {
            RCLCPP_INFO(this->get_logger(), "Configuring LED Colour Controller");

            pub_ = this->create_publisher<std_msgs::msg::ColorRGBA>("led_colour", 10);

            timer_ = this->create_wall_timer(1s, std::bind(&LedColourControllerNode::publish_random_colour, this));
            timer_->cancel(); // Start with the timer stopped

            publish_colour(255, 255, 0); // Turn to yellow after configuring

            return LifecycleCallback::SUCCESS;
        }

        LifecycleCallback on_activate(const rclcpp_lifecycle::State &state) {
            RCLCPP_INFO(this->get_logger(), "Activating LED Colour Controller");

            LifecycleNode::on_activate(state);

            timer_->reset(); // Resume timer on activate

            return LifecycleCallback::SUCCESS;
        }

        LifecycleCallback on_deactivate(const rclcpp_lifecycle::State &state) {
            RCLCPP_INFO(this->get_logger(), "Deactivating LED Colour Controller");

            LifecycleNode::on_deactivate(state);

            timer_->cancel();

            publish_colour(255, 0, 0); // Turn to red on deactivate

            return LifecycleCallback::SUCCESS;
        }

        LifecycleCallback on_cleanup(const rclcpp_lifecycle::State &state) {
            RCLCPP_INFO(this->get_logger(), "Cleaning up LED Colour Controller");

            timer_.reset();
            pub_.reset();

            return LifecycleCallback::SUCCESS;
        }

        LifecycleCallback on_shutdown(const rclcpp_lifecycle::State &state) {
            RCLCPP_INFO(this->get_logger(), "Shuting down LED Colour Controller");

            timer_.reset();
            pub_.reset();

            return LifecycleCallback::SUCCESS;
        }

    private:
        void publish_colour(float r, float g, float b, float a = 0) {
            auto colour = std::make_unique<std_msgs::msg::ColorRGBA>();
            colour->r = r;
            colour->g = g;
            colour->b = b;
            colour->a = a;

            RCLCPP_INFO(this->get_logger(), "Publishing colour: R(%f), G(%f), B(%f), a(%f)", 
                colour->r,
                colour->g,
                colour->b,
                colour->a
            );
            
            pub_->publish(std::move(colour));
        };
        void publish_random_colour() {
            publish_colour(rand() % 256, rand() % 256, rand() % 256);
        };

        // Using regular publisher to allow colour changing in inactive state
        std::shared_ptr<rclcpp::Publisher<std_msgs::msg::ColorRGBA>> pub_;
        std::shared_ptr<rclcpp::TimerBase> timer_;
};

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);

    rclcpp::executors::SingleThreadedExecutor executor;
    auto node = std::make_shared<LedColourControllerNode>("led_colour_controller_node");

    executor.add_node(node->get_node_base_interface());
    executor.spin();

    rclcpp::shutdown();
    return 0;
}