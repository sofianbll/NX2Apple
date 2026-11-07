import Foundation
import ImageIO
import NXCore
import UniformTypeIdentifiers

/// The pixel side of applying an icon: the same aspect-fill crop as the artwork views, rendered at 1024 px and converted by iconutil.
enum MacAppIconImage {
    private static let sizes = [16, 32, 128, 256, 512]

    static func render(source: URL, output: URL, focusX: Double, focusY: Double, runner: ProcessRunner) throws -> Int {
        let cropped = try square(source: source, focusX: focusX, focusY: focusY)
        let iconset = output.deletingLastPathComponent().appendingPathComponent("AppIcon.iconset", isDirectory: true)
        try FileManager.default.createDirectory(at: iconset, withIntermediateDirectories: true)
        for size in sizes {
            for scale in [1, 2] {
                let pixels = size * scale
                let name = "icon_\(size)x\(size)\(scale == 2 ? "@2x" : "").png"
                try write(png: resized(cropped.image, pixels: pixels), to: iconset.appendingPathComponent(name))
            }
        }
        guard runner.runOK("/usr/bin/iconutil", ["-c", "icns", iconset.path, "-o", output.path]) else { throw MacAppIcon.Failure.applyFailed }
        return cropped.cropSide
    }

    /// A square aspect-fill crop. Focus 0 is the leading or top edge, exactly as ArtworkFraming presents it.
    static func square(source: URL, focusX: Double, focusY: Double) throws -> (image: CGImage, cropSide: Int) {
        guard let input = CGImageSourceCreateWithURL(source as CFURL, nil),
              let properties = CGImageSourceCopyPropertiesAtIndex(input, 0, nil) as? [CFString: Any],
              let width = properties[kCGImagePropertyPixelWidth] as? Int, let height = properties[kCGImagePropertyPixelHeight] as? Int,
              width > 0, height > 0 else { throw MacAppIcon.Failure.unreadable }
        let options: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: max(width, height),
        ]
        guard let image = CGImageSourceCreateThumbnailAtIndex(input, 0, options as CFDictionary),
              CGImageSourceGetStatusAtIndex(input, 0) == .statusComplete else { throw MacAppIcon.Failure.unreadable }
        let cropSide = min(image.width, image.height)
        if let rejection = MacAppIcon.rejection(hasChoice: true, cropSide: cropSide, running: false) { throw rejection }
        let context = try context(width: 1024, height: 1024)
        let scale = 1024 / CGFloat(cropSide)
        let drawn = CGSize(width: CGFloat(image.width) * scale, height: CGFloat(image.height) * scale)
        let x = (1024 - drawn.width) * min(max(CGFloat(focusX), 0), 1)
        let y = (1024 - drawn.height) * (1 - min(max(CGFloat(focusY), 0), 1))
        context.interpolationQuality = .high
        context.draw(image, in: CGRect(origin: CGPoint(x: x, y: y), size: drawn))
        guard let square = context.makeImage() else { throw MacAppIcon.Failure.unreadable }
        return (square, cropSide)
    }

    private static func resized(_ image: CGImage, pixels: Int) throws -> CGImage {
        let context = try context(width: pixels, height: pixels)
        context.interpolationQuality = .high
        context.draw(image, in: CGRect(x: 0, y: 0, width: pixels, height: pixels))
        guard let resized = context.makeImage() else { throw MacAppIcon.Failure.unreadable }
        return resized
    }

    private static func context(width: Int, height: Int) throws -> CGContext {
        guard let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: 0,
                                      space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue) else {
            throw MacAppIcon.Failure.unreadable
        }
        return context
    }

    private static func write(png image: CGImage, to url: URL) throws {
        guard let destination = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
            throw MacAppIcon.Failure.unreadable
        }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else { throw MacAppIcon.Failure.unreadable }
    }
}
