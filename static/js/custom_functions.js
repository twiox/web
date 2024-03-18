function _calculateAge(birthday, checkDate) { // birthday is a date
    var ageDifMs = checkDate.getTime() - birthday.getTime();
    var ageDate = new Date(ageDifMs); // miliseconds from epoch
    return Math.abs(ageDate.getUTCFullYear() - 1970);
}