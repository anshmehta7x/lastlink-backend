export function validateEmail(email: string): boolean {
    if (email.length > 200) {
        return false;
    }
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

export function validateUsername(uname: string): boolean {
    if (uname.length > 30) {
        return false;
    }
    if (uname.length < 3) {
        return false;
    }
    const regex = /^[a-zA-Z0-9_]+$/;
    if (!regex.test(uname)) {
        return false;
    }
    return true;
}
