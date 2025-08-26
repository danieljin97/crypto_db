import polars as pl
import os
import time 

def qa_report(df: pl.DataFrame, file_name: str, log_to_file: bool = True):
    """
    Generate a QA report for table.

    Parameters
    ----------
    df : pl.DataFrame
        The dataset to analyze.

    file_name : str
        Name of the source file.
    
    log_to_file : bool
        If True, saves the report as a .txt log file.
    """

    # Prepare report as a string
    report_lines = []
    report_lines.append("="*50)
    report_lines.append(f"📊 QA Report for {file_name}")
    report_lines.append("="*50)

    # Shape
    report_lines.append(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")

    # Column types
    report_lines.append("\nColumns and Data Types:")
    for col in df.columns:
        report_lines.append(f" - {col}: {df[col].dtype}")

    # Null counts
    report_lines.append("\nNull Counts:")
    report_lines.append(str(df.null_count()))

    # Duplicate check
    dup_count = df.is_duplicated().sum()
    report_lines.append(f"\nDuplicate rows: {dup_count}")

    # Basic statistics
    try:
        report_lines.append("\nBasic Statistics:")
        report_lines.append(str(df.describe()))
    except Exception:
        report_lines.append("\nBasic Statistics: (Could not compute)")

    # Freshness check if timestamp exists
    if "timestamp" in df.columns:
        max_ts = df["timestamp"].max()
        report_lines.append(f"\nMost recent timestamp: {max_ts}")

    # Final report text
    report = "\n".join(report_lines)

    # Print to console
    print(report)

    # Optionally save to file
    if log_to_file:
        os.makedirs("qa_logs", exist_ok=True)
        log_path = f"qa_logs/{file_name}_qa.txt"
        with open(log_path, "w") as f:
            f.write(report)
        print(f"\nQA report saved to {log_path}")





