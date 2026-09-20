#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include "libfairino/include/robot.h"

static void usage(const char * name)
{
  std::cerr << "Usage: " << name << " --ip IP --index N [--percent 0..100] [--read]\n";
}

int main(int argc, char ** argv)
{
  std::string ip;
  int index = 1;
  int percent = -1;
  bool read = false;
  for (int i = 1; i < argc; ++i) {
    const std::string arg(argv[i]);
    auto value = [&](const char * option) {
      if (i + 1 >= argc) throw std::runtime_error(std::string("Missing value for ") + option);
      return std::string(argv[++i]);
    };
    if (arg == "--ip") ip = value("--ip");
    else if (arg == "--index") index = std::stoi(value("--index"));
    else if (arg == "--percent") percent = std::stoi(value("--percent"));
    else if (arg == "--read") read = true;
    else { usage(argv[0]); return 2; }
  }
  if (ip.empty() || index < 1 || index > 8 || percent < -1 || percent > 100 || (!read && percent < 0)) {
    usage(argv[0]); return 2;
  }

  FRRobot robot;
  const int rpc = robot.RPC(ip.c_str());
  if (rpc != 0) { std::cerr << "RPC failed: " << rpc << '\n'; return 1; }
  const int activated = robot.ActGripper(index, 1);
  if (activated != 0) { std::cerr << "ActGripper failed: " << activated << '\n'; return 1; }
  if (read) {
    std::uint16_t fault = 0;
    std::uint8_t position = 0;
    const int result = robot.GetGripperCurPosition(&fault, &position);
    if (result != 0 || fault != 0) {
      std::cerr << "GetGripperCurPosition failed: code=" << result << " fault=" << fault << '\n';
      return 1;
    }
    std::cout << static_cast<int>(position) << '\n';
  }
  if (percent >= 0) {
    const int result = robot.MoveGripper(index, percent, 50, 50, 30000, 1, 0, 0.0, 0, 0);
    if (result != 0) { std::cerr << "MoveGripper failed: " << result << '\n'; return 1; }
  }
  robot.CloseRPC();
  return 0;
}
