import AppKit
import ImageIO
import UniformTypeIdentifiers
import XCTest
@testable import NX2Apple
@testable import NXCore

final class MacAppIconImageTests: XCTestCase {
    private var temporary: URL!

    override func setUpWithError() throws {
        temporary = FileManager.default.temporaryDirectory.appendingPathComponent("nx2apple-icon-image-" + UUID().uuidString)
        try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws { try FileManager.default.removeItem(at: temporary) }

    private func image(width: Int, height: Int) throws -> URL {
        let context = try XCTUnwrap(CGContext(data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: 0,
                                              space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue))
        context.setFillColor(CGColor(red: 1, green: 0, blue: 0, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: width / 2, height: height))
        context.setFillColor(CGColor(red: 0, green: 0, blue: 1, alpha: 1))
        context.fill(CGRect(x: width / 2, y: 0, width: width - width / 2, height: height))
        let url = temporary.appendingPathComponent("source.jpg")
        let destination = try XCTUnwrap(CGImageDestinationCreateWithURL(url as CFURL, UTType.jpeg.identifier as CFString, 1, nil))
        CGImageDestinationAddImage(destination, try XCTUnwrap(context.makeImage()), nil)
        XCTAssertTrue(CGImageDestinationFinalize(destination))
        return url
    }

    private func firstPixel(_ image: CGImage) throws -> (red: UInt8, blue: UInt8) {
        let data = try XCTUnwrap(image.dataProvider?.data as Data?)
        return (data[0], data[2])
    }

    func testSquareCropIs1024AndFollowsTheHorizontalFocus() throws {
        let source = try image(width: 1024, height: 512)
        let left = try MacAppIconImage.square(source: source, focusX: 0, focusY: 0.5)
        let right = try MacAppIconImage.square(source: source, focusX: 1, focusY: 0.5)
        XCTAssertEqual(left.image.width, 1024)
        XCTAssertEqual(left.image.height, 1024)
        XCTAssertEqual(left.cropSide, 512)
        XCTAssertGreaterThan(try firstPixel(left.image).red, try firstPixel(left.image).blue)
        XCTAssertGreaterThan(try firstPixel(right.image).blue, try firstPixel(right.image).red)
    }

    func testSquareCropRefusesAnImageBelow512() throws {
        XCTAssertThrowsError(try MacAppIconImage.square(source: image(width: 800, height: 400), focusX: 0.5, focusY: 0.5)) {
            XCTAssertEqual($0 as? MacAppIcon.Failure, .cropTooSmall)
        }
    }

    func testRenderBuildsEveryRequiredIconRepresentation() throws {
        let output = temporary.appendingPathComponent("AppIcon.icns")
        let side = try MacAppIconImage.render(source: image(width: 1024, height: 512), output: output, focusX: 0.5, focusY: 0.5,
                                              runner: SystemProcessRunner())
        XCTAssertEqual(side, 512)
        let source = try XCTUnwrap(CGImageSourceCreateWithURL(output as CFURL, nil))
        XCTAssertEqual(CGImageSourceGetCount(source), 10)
        let icon = try XCTUnwrap(NSImage(contentsOf: output))
        XCTAssertTrue(icon.representations.contains { $0.pixelsWide == 1024 && $0.pixelsHigh == 1024 })
    }
}
