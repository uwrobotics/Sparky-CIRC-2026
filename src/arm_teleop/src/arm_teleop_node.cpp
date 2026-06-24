#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joy.hpp>
#include <odrive_can/msg/control_message.hpp>

// XBox 360 indicies
constexpr int AXIS_LEFT_X = 0; // A1 Base Rotation
constexpr int AXIS_LEFT_Y = 1; // A2 Shoulder Rotation 
constexpr int AXIS_RIGHT_X = 2; // A3 Elbow Rotation 
constexpr int AXIS_RIGHT_Y = 4; // A4 Forearm Twist
constexpr int AXIS_LT = 5; // Gripper claw close
constexpr int AXIS_RT = 6; // Gripper claw open
constexpr int AXIS_DPAD_X = 7; // A5 Wrist Pitch
constexpr int AXIS_DPAD_Y = 8; // A6 Wrist Roll
constexpr int BTN_A     = 0;
constexpr int BTN_B     = 1;
constexpr int BTN_START = 7;
constexpr int BTN_LB    = 4;
constexpr int CONTROL_MODE_VELOCITY  = 2;
constexpr int INPUT_MODE_PASSTHROUGH = 1;

// Todo: Replace with real ODrive topic names
const std::vector<std::string> JOINT_TOPICS = {
    "/odrive_axis0/control_message",  // J1 - base
    "/odrive_axis1/control_message",  // J2 - shoulder
    "/odrive_axis2/control_message",  // J3 - elbow
    "/odrive_axis3/control_message",  // J4 - forearm
    "/odrive_axis4/control_message",  // J5 - wrist pitch
    "/odrive_axis5/control_message",  // J6 - wrist roll
};

class ArmTeleopNode : public rclcpp::Node{
    public: 
        ArmTeleopNode() : Node("arm_teleop_node"){
            this->declare_parameter("max_velocity_slow", 0.5); 
            this->declare_parameter("max_velocity_fast", 1.5);
            this->declare_parameter("deadband", 0.08);
            this->declare_parameter("dpad_velocity", 0.3);
            this->declare_parameter("gripper_velocity", 0.5);

            max_vel_slow_ = this->get_parameter("max_velocity_slow").as_double();
            max_vel_fast_ = this->get_parameter("max_velocity_fast").as_double();
            deadband_ = this->get_parameter("deadband").as_double();
            dpad_velocity_ = this->get_parameter("dpad_velocity").as_double();
            gripper_velocity_ = this->get_parameter("gripper_velocity").as_double();

            for(const auto & topic :JOINT_TOPICS){
                joint_pubs_.push_back(
                    this->create_publisher<odrive_can::msg::ControlMessage>(topic, 10)
                );
            }

            joy_sub_ = this->create_subscription<sensor_msgs::msg::Joy>(
                "/joy",
                10,
                std::bind(&ArmTeleopNode::joy_callback, this, std::placeholders::_1)
            );

            RCLCPP_INFO(this->get_logger(), "Arm teleop ready. Press A to enable. B for e-stop. START to re-arm.");
        }

        ~ArmTeleopNode() { publish_zeros(); }

    private:
        bool enabled_ = false; 
        bool estopped_ = false;
        bool fast_mode_ = false; 
        bool prev_btn_a_ = false; 
        bool prev_btn_b_ = false;
        bool prev_btn_start_ = false;
        bool prev_btn_lb_ = false;

        double max_vel_slow_;
        double max_vel_fast_;
        double deadband_;
        double dpad_velocity_;
        double gripper_velocity_;

        rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr joy_sub_;
        std::vector<rclcpp::Publisher<odrive_can::msg::ControlMessage>::SharedPtr> joint_pubs_;

        double deadband(double val) const{
            if(std::abs(val) > deadband_){
                return val;
            }else{
                return 0.0;
            }
        }

        double normalize_trigger(double raw) const{
            return (raw + 1.0)/2.0;
        }

        void publish_velocity(size_t joint_idx, double velocity){
            if(joint_idx >= joint_pubs_.size()){
                return;
            }
            odrive_can::msg::ControlMessage msg;
            msg.control_mode = CONTROL_MODE_VELOCITY;
            msg.input_mode = INPUT_MODE_PASSTHROUGH;
            msg.input_vel = static_cast<float>(velocity);
            msg.input_pos = 0.0f;
            msg.input_torque = 0.0f;
            joint_pubs_[joint_idx]->publish(msg);
        }

        void publish_zeros(){
            for(size_t i = 0; i < joint_pubs_.size(); ++i){
                publish_velocity(i, 0.0);
            }
        }

        void joy_callback(const sensor_msgs::msg::Joy::SharedPtr msg){
            bool btn_a = msg->buttons[BTN_A];
            bool btn_b = msg->buttons[BTN_B];
            bool btn_start = msg->buttons[BTN_START];
            bool btn_lb = msg->buttons[BTN_LB];

            // A btn: toggle enabled
            if(btn_a && !prev_btn_a_){
                if(!estopped_){
                    enabled_ = !enabled_;
                    RCLCPP_INFO(this->get_logger(), "Tele-op is %s", enabled_ ? "ENABLED" : "DISABLED");
                } else{
                    RCLCPP_WARN(this->get_logger(), "ESTOP active, press start to re-arm first");
                }
            }

            // B btn: estopped
            if(btn_b && !prev_btn_b_){
                estopped_ = true;
                enabled_ = false;
                publish_zeros();
                RCLCPP_ERROR(this->get_logger(), " ESTOP! Press START to re-arm the arm");
            }

            // START btn: rearm
            if(btn_start && !prev_btn_start_ && estopped_){
                estopped_ = false;
                RCLCPP_INFO(this->get_logger(), "Re-armed,press a to enable");
            }

            // LB btn: speed toggle
            if(btn_lb && !prev_btn_lb_){
              fast_mode_ = !fast_mode_;
              RCLCPP_INFO(this->get_logger(), "Speed: %s", fast_mode_ ? "FAST" : "SLOW");
            }

            prev_btn_a_ = btn_a;
            prev_btn_b_ = btn_b;
            prev_btn_lb_ = btn_lb;
            prev_btn_start_ = btn_start;

            if(!enabled_ || estopped_){
                publish_zeros();
                return;
            }

            double scale; 
            if(fast_mode_){
                scale = max_vel_fast_;
            }else{
                scale = max_vel_slow_;
            }

            double j1 = deadband(msg->axes[AXIS_LEFT_X]) * scale;
            double j2 = -deadband(msg->axes[AXIS_LEFT_Y]) * scale;
            double j3 = deadband(msg->axes[AXIS_RIGHT_X]) * scale;
            double j4 = -deadband(msg->axes[AXIS_RIGHT_Y]) * scale;
            double j5 = msg->axes[AXIS_DPAD_Y] * dpad_velocity_; 
            double j6 = msg->axes[AXIS_DPAD_X] * dpad_velocity_;

            double lt = normalize_trigger(msg->axes[AXIS_LT]);
            double rt = normalize_trigger(msg->axes[AXIS_RT]);
            // + => close
            // - => open
            double gripper = (lt - rt) * gripper_velocity_;
            publish_velocity(0, j1);
            publish_velocity(1, j2);
            publish_velocity(2, j3);
            publish_velocity(3, j4);
            publish_velocity(4, j5);
            publish_velocity(5, j6);

            // TODO: wire gripper to its actual topic
            (void)gripper;
        }
};

int main(int argc, char * argv[]){
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ArmTeleopNode>());
  rclcpp::shutdown();
  return 0;
}
