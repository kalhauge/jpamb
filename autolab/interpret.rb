
module InterpretAssignment

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
    "<th>Nickname</th><th>Version</th><th>Time</th><th>Total</th>"
end

def createScoreboardEntry(scores, autoresult)
    
    total = scores["Total"].to_f()

    return [total]
end

end
