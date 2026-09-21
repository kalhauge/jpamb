
module AnalyseAssignment

def assessmentVariables
    variables = {}
    variables["previous_submissions_lookback"] = 100
    variables["exclude_autograding_in_progress_submissions"] = false
    variables
end

def raw_score(score)

    total = score["Total"].to_f()

    return total
end

def scoreboardHeader
    "<th>Nickname</th><th>Version</th><th>Time</th><th>Total</th><th>RelativeTime</th><th>Categories</th><th>Pass</th>"
end

def createScoreboardEntry(scores, autoresult)
    
    total = scores["Total"].to_f()
    reltime = scores["Time"].to_f()
    categories = scores["Categories"].to_f()
    pass = total >= 100 ? "Yes" : "No"

    return [total, reltime, categories, pass]
end

end
