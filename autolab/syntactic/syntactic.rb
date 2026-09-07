
module AnalysisAssessment

def assessmentVariables
    variables = {}
    variables["previous_submissions_lookback"] = 100
    variables["exclude_autograding_in_progress_submissions"] = false
    variables
end

def raw_score(score)

    simple = score["Simple"].to_f()
    arrays = score["Arrays"].to_f()
    loops = score["Loops"].to_f()
    calls = score["Calls"].to_f()
    tricky = score["Tricky"].to_f()
    string = score["Strings"].to_f()
    dependent = score["Dependent"].to_f()

    return simple + arrays + loops + calls + tricky + string + dependent
end

def scoreboardHeader
    "<th>Nickname</th><th>Version</th><th>Time</th><th>Total</th><th>Simple</th><th>Arrays</th><th>Calls</th><th>Loops</th><th>Tricky</th><th>Strings</th><th>Dependent</th><th>RelativeTime</th>"
end

def createScoreboardEntry(scores, autoresult)

    reltime = scores["RelativeTime"].to_f()
    simple = scores["Simple"].to_f()
    arrays = scores["Arrays"].to_f()
    loops = scores["Loops"].to_f()
    calls = scores["Calls"].to_f()
    tricky = scores["Tricky"].to_f()
    strings =  scores["Strings"].to_f()
    dependent =  scores["Dependent"].to_f()
    total = raw_score(scores)

    return [total, simple, arrays, loops, calls, tricky, strings, dependent, reltime]
end

end
