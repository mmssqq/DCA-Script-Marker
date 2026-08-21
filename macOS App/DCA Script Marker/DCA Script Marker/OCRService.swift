// Copyright © 2026 马斯琪 Siqi Ma
// SPDX-License-Identifier: AGPL-3.0-or-later

import AppKit
import Foundation
import PDFKit
import Vision

/// Reads scanned PDF pages with macOS's built-in Vision text recognition.
/// The resulting JSON stays in a temporary folder and is used only for the
/// current export; the user's PDF is never changed.
enum OCRService {
    private struct OCRLine: Codable {
        let text: String
        let bbox: [Double]
    }

    private struct OCRPage: Codable {
        let lines: [OCRLine]
    }

    static func recognise(
        pdfURL: URL,
        progress: @escaping (Int, Int) -> Void
    ) throws -> URL {
        guard let document = PDFDocument(url: pdfURL) else {
            throw NSError(
                domain: "DCA Script Marker",
                code: 1,
                userInfo: [
                    NSLocalizedDescriptionKey: "The scanned PDF could not be opened."
                ]
            )
        }

        var ocrPages: [OCRPage] = []

        for pageIndex in 0..<document.pageCount {
            guard let page = document.page(at: pageIndex) else {
                ocrPages.append(OCRPage(lines: []))
                continue
            }

            let bounds = page.bounds(for: .mediaBox)
            let scale = max(2.0, min(3.0, 1800.0 / max(bounds.width, 1)))
            let renderedSize = CGSize(
                width: bounds.width * scale,
                height: bounds.height * scale
            )

            // PDFKit's thumbnail renderer keeps the page orientation and
            // colour profile that Vision expects.  A manually created bitmap
            // can look correct on screen but arrive blank to Vision.
            let renderedImage = page.thumbnail(
                of: renderedSize,
                for: .mediaBox
            )
            guard let image = renderedImage.cgImage(
                forProposedRect: nil,
                context: nil,
                hints: nil
            ) else {
                ocrPages.append(OCRPage(lines: []))
                continue
            }

            let request = VNRecognizeTextRequest()
            request.recognitionLevel = .accurate
            request.usesLanguageCorrection = true
            request.recognitionLanguages = ["en-US", "zh-Hans"]
            request.minimumTextHeight = 0.01

            let handler = VNImageRequestHandler(cgImage: image, options: [:])
            try handler.perform([request])

            let lines = (request.results ?? []).compactMap { observation -> OCRLine? in
                guard let candidate = observation.topCandidates(1).first else {
                    return nil
                }

                let box = observation.boundingBox
                // Vision coordinates are bottom-left based; PDF text boxes
                // are top-left based.
                return OCRLine(
                    text: candidate.string,
                    bbox: [
                        Double(box.minX) * Double(bounds.width),
                        Double(1 - box.maxY) * Double(bounds.height),
                        Double(box.width) * Double(bounds.width),
                        Double(box.height) * Double(bounds.height),
                    ]
                )
            }.sorted {
                abs($0.bbox[1] - $1.bbox[1]) < 5
                    ? $0.bbox[0] < $1.bbox[0]
                    : $0.bbox[1] < $1.bbox[1]
            }

            ocrPages.append(OCRPage(lines: lines))
            progress(pageIndex + 1, document.pageCount)
        }

        let outputURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("DCA-Script-Marker-OCR.json")
        let data = try JSONEncoder().encode(ocrPages)
        try data.write(to: outputURL, options: .atomic)
        return outputURL
    }
}
