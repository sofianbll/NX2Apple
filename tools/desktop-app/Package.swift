// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "NXNativeDashboard",
    platforms: [.macOS(.v13)],
    targets: [
        .target(name: "NXNativeCore"),
        .executableTarget(name: "NXNativeDashboard", dependencies: ["NXNativeCore"]),
        .testTarget(name: "NXNativeCoreTests", dependencies: ["NXNativeCore"]),
    ]
)
