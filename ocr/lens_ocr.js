import fs from 'fs';
import { createRequire } from 'module';

// The main github is: https://github.com/dimdenGD/chrome-lens-ocr.git, please clone it into this folder

// --- HOT PATCH CHROME-LENS-OCR ---
// We need the rotation angle to correctly draw bounding boxes for rotated text.
// chrome-lens-ocr drops this field, so we monkey-patch it before importing.
const require = createRequire(import.meta.url);
const corePath = require.resolve('chrome-lens-ocr/src/core.js');
let coreCode = fs.readFileSync(corePath, 'utf8');
let patched = false;
if (coreCode.includes('box.length !== 4')) {
    coreCode = coreCode.replace(/box\.length !== 4/g, 'box.length < 4');
    patched = true;
}
if (!coreCode.includes('protoGeoBox.getRotationZ()')) {
    coreCode = coreCode.replace(
        /const boxData = \[\s*protoGeoBox\.getCenterX\(\),\s*protoGeoBox\.getCenterY\(\),\s*protoGeoBox\.getWidth\(\),\s*protoGeoBox\.getHeight\(\)\s*\];/g,
        'const boxData = [protoGeoBox.getCenterX(), protoGeoBox.getCenterY(), protoGeoBox.getWidth(), protoGeoBox.getHeight(), protoGeoBox.getRotationZ ? protoGeoBox.getRotationZ() : 0];'
    );
    coreCode = coreCode.replace(
        /this\.perHeight = box\[3\];/g,
        'this.perHeight = box[3];\n        this.rotationZ = box[4] || 0;'
    );
    patched = true;
}
if (patched) {
    fs.writeFileSync(corePath, coreCode);
}
// ---------------------------------

async function main() {
    const { default: Lens } = await import('chrome-lens-ocr');

    const filePath = process.argv[2];
    if (!filePath) {
        console.error("Usage: node lens_ocr.js <file_path>");
        process.exit(1);
    }

    if (!fs.existsSync(filePath)) {
        console.error(`File not found: ${filePath}`);
        process.exit(1);
    }

    try {
        const lens = new Lens();
        const result = await lens.scanByFile(filePath);

        let segments = result.segments || [];

        // --- SORTING LOGIC ---
        // Lens API results can be out of order. We sort them by row, then by column.
        // We also handle rotated images by calculating a dominant rotation and transforming coordinates.
        if (segments.length > 1) {
            const validSegments = segments.filter(s => s.boundingBox);
            const invalidSegments = segments.filter(s => !s.boundingBox);

            if (validSegments.length > 0) {
                // Detect dominant rotation (in radians)
                const rotations = validSegments.map(s => s.boundingBox.rotationZ || 0);
                const bucketSize = Math.PI / 8; // 22.5 degrees buckets
                const buckets = {};
                rotations.forEach(r => {
                    const bucket = Math.round(r / bucketSize);
                    buckets[bucket] = (buckets[bucket] || 0) + 1;
                });
                let dominantBucket = 0;
                let maxCount = -1;
                for (const b in buckets) {
                    if (buckets[b] > maxCount) {
                        maxCount = buckets[b];
                        dominantBucket = parseInt(b);
                    }
                }
                const theta = dominantBucket * bucketSize;
                const cosT = Math.cos(-theta);
                const sinT = Math.sin(-theta);

                // Add rotated coordinates for sorting
                validSegments.forEach(s => {
                    const x = s.boundingBox.centerPerX;
                    const y = s.boundingBox.centerPerY;
                    s._xRot = x * cosT - y * sinT;
                    s._yRot = x * sinT + y * cosT;
                });

                // 1. Sort by Y rotated (lines)
                validSegments.sort((a, b) => a._yRot - b._yRot);

                // 2. Group into lines
                const lines = [];
                let currentLine = [validSegments[0]];
                lines.push(currentLine);
                for (let i = 1; i < validSegments.length; i++) {
                    const prev = currentLine[currentLine.length - 1];
                    const curr = validSegments[i];
                    // Threshold: half of average segment height
                    const heightAvg = (prev.boundingBox.perHeight + curr.boundingBox.perHeight) / 2;

                    if (Math.abs(curr._yRot - prev._yRot) < heightAvg * 0.5) {
                        currentLine.push(curr);
                    } else {
                        currentLine = [curr];
                        lines.push(currentLine);
                    }
                }

                // 3. Sort within lines by X rotated
                lines.forEach(line => line.sort((a, b) => a._xRot - b._xRot));

                // 4. Flatten back
                segments = [...lines.flat(), ...invalidSegments];
            }
        }
        // ---------------------

        // Combine all text segments into a single string
        const fullText = segments.map(s => s.text).join(' ');

        const output = {
            full_text: fullText,
            segments: segments.map(s => ({
                text: s.text,
                box: s.boundingBox ? {
                    x: s.boundingBox.centerPerX - (s.boundingBox.perWidth / 2),
                    y: s.boundingBox.centerPerY - (s.boundingBox.perHeight / 2),
                    width: s.boundingBox.perWidth,
                    height: s.boundingBox.perHeight,
                    rotation: s.boundingBox.rotationZ || 0
                } : null
            }))
        };

        process.stdout.write(JSON.stringify(output));
    } catch (error) {
        console.error(`Lens OCR Error: ${error.message}`);
        process.exit(1);
    }
}

main();
