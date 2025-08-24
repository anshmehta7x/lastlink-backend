export function validateURL(url: string) {
    const urlRegex = /^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:\/[^\s]*)?$/;
    return urlRegex.test(url.trim());
}
