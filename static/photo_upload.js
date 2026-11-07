// Photos of paper forms taken by trainers (consent, membership application): shrunk before upload
// to a JPEG of at most 1600 px, which keeps forms readable at a few hundred KB.
// Falls back to the original file if the browser cannot decode it.
async function shrinkPhoto(file, max = 1600) {
    try {
        const image = await createImageBitmap(file);  // follows the photo's orientation
        const scale = Math.min(1, max / Math.max(image.width, image.height));
        const canvas = document.createElement('canvas');
        canvas.width = Math.round(image.width * scale);
        canvas.height = Math.round(image.height * scale);
        canvas.getContext('2d').drawImage(image, 0, 0, canvas.width, canvas.height);
        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8));
        return blob || file;
    } catch (err) {
        return file;
    }
}
