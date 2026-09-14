# Workflow Results Dashboard

The Job Automation workflow writes a machine-readable daily report and uploads it as a GitHub Actions artifact.

## View all workflow runs

Open the repository's **Actions** tab and select **Production Job Hunter**.

Each run contains:

- Job discovery count
- Eligible-job count
- High-match count
- Application queue count
- Collector results
- Top matching jobs
- Deadline information
- Errors/warnings
- Execution duration

## View a specific run

1. Open **Actions**.
2. Select **Production Job Hunter**.
3. Select any workflow run.
4. Open the **Artifacts** section.
5. Download `daily-job-report-<run-number>`.

## Machine-readable output

The report is also generated at `daily-report.txt` during each run.

## Historical data

Long-term job/application history belongs in PostgreSQL. GitHub Actions artifacts are retained for 30 days by the workflow unless repository retention settings change.
