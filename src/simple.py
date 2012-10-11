import cds_settings
import db

def ProcessSimpleResult(simpleId, simpleResult):
    '''
    Process a special case simple results.

    simpleResult parameter should be a tuple of 2
    '''

    if simpleId == cds_settings.SIMPLE_ID_BIG_SHOW:
        ProcessBigShowResult(simpleResult)

    elif simpleId == cds_settings.SIMPLE_ID_FEEDBACK:
        ProcessFeedbackResult(simpleResult)

def ProcessFeedbackResult(result):
    isSucceeded = result[0]
    feedback = result[1]
    if not isSucceeded:
        db.IncrementFeedback('cancel')
        return

    if feedback == 0:
        db.IncrementFeedback('no')
    elif feedback == 1:
        db.IncrementFeedback('yes')
    else:
        db.IncrementFeedback('cancel')


def ProcessBigShowResult(result):
    '''
    A big show is considered shown when the result is (1,1) only
    '''

    isSucceeded = result[0]
    wasShown = result[1]

    if isSucceeded and wasShown:
        db.SetBigShowShown()
    else:
        db.CancelLastAllowedTime()
