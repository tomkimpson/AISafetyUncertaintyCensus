# Developer right-of-reply protocol

## Scope

Before submission, invite Anthropic, OpenAI, and Google DeepMind to check
source-attribution and factual reporting claims about their public documents.
Invite the third-party evaluators named in the model-level audit when a claim
depends materially on their report. This is a factual review, not editorial
approval and not a request to endorse the paper's analysis.

## Procedure

1. Freeze a dated review draft and the derived CSV checksums.
2. Send each organisation only the rows and prose claims that concern its
   documents, plus links to the full draft and public repository.
3. Ask for:
   - corrections to document identity, version, locator, copied score,
     denominator, uncertainty statement, or threshold;
   - a pointer to public uncertainty information missed by the census;
   - clarification of whether a displayed `±` is SD, SE, a confidence interval,
     or another quantity; and
   - permission to quote any non-public response. Treat responses as
     off-the-record unless permission is explicit.
4. Allow at least 14 calendar days and state the deadline in the first message.
   Send one reminder after seven days.
5. Log the date, recipient role or public contact channel, response status, and
   resulting change in a private outreach log. Do not commit personal email
   addresses or non-public correspondence.
6. Correct verified factual errors regardless of whether they affect the
   headline result. Record substantive changes in the public changelog without
   disclosing private correspondence.
7. In the manuscript, report the process and response count neutrally. A
   non-response is not agreement.

## Decision rule for responses

- Public-source correction: update the source locator or coding, regenerate the
  analysis, and cite the public evidence.
- Clarification not present in a public source: retain the public-document
  coding, note the clarification separately only with permission, and avoid
  treating it as retrospectively published evidence.
- Disagreement about interpretation: state both interpretations when material
  and show the corresponding sensitivity.
- Request to suppress an accurate public-source finding: decline, while
  correcting tone or context if warranted.

The reusable message is in `docs/outreach/developer_review_template.md`.
