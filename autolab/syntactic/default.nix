{
  name = "syntactic";
  general = {
    category_name = "Syntactic";
    display_name = "Syntactic Assignment";
  };

  dates = {
    due_at = "2026-09-13 23:59:59 +0200";
    end_at = "2026-09-30 11:53:32 +0200";
    start_at = "2026-09-08 11:53:32 +0200";
  };

  problems = [
    {
      name = "Total";
      max_score = 46.0 * 6.0;
      description = "The total score";
    }
    {
      name = "Time";
      max_score = 100.0;
      description = "100 / mean relative time";
    }
    {
      name = "Categories";
      max_score = 100.0;
      description = "100 / number of categories used";
    }
  ];
}
