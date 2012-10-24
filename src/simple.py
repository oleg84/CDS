import cds_settings
import db
import listeners



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
    Big show is considered started, when result[0] is 1. The result[1] in this case is the show ID
    '''

    isSucceeded = result[0]
    bigShowId = result[1]

    if isSucceeded:
        db.SetBigShowShown()
        listeners.StartBigShow(bigShowId)
    else:
        db.CancelLastAllowedTime()
