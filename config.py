#maximum number of servings allowed when a recipe is scaled:
#50 + the last two digits of the faculty number 2301262031 -> 50 + 31 = 81
FACULTY_NUMBER = "2301262031"
MAX_SERVINGS = 50 + int(FACULTY_NUMBER[-2:])
