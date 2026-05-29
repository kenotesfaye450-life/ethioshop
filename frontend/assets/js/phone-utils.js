/** Shared Ethiopian phone normalization (09 / 07, 10 digits). */
const ETHIOPIAN_PHONE_REGEX = /^(09|07)[0-9]{8}$/;

function normalizeEthiopianPhone(phone) {
    if (!phone) return null;
    let digits = String(phone).trim().replace(/\D/g, '');
    if (digits.startsWith('251')) {
        digits = '0' + digits.slice(3);
    }
    if (!ETHIOPIAN_PHONE_REGEX.test(digits)) {
        return null;
    }
    return digits;
}

function isValidEthiopianPhone(phone) {
    return normalizeEthiopianPhone(phone) !== null;
}
