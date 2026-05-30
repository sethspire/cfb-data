data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "backfill" {
  name               = "cfb-data-backfill-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

resource "aws_iam_policy" "bronze_writer" {
  name        = "cfb-data-bronze-writer"
  description = "Write access to the bronze S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
        ]
        Resource = [
          "arn:aws:s3:::${var.bucket_name}",
          "arn:aws:s3:::${var.bucket_name}/*",
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "bronze_writer" {
  role       = aws_iam_role.backfill.name
  policy_arn = aws_iam_policy.bronze_writer.arn
}

resource "aws_iam_instance_profile" "backfill" {
  name = "cfb-data-backfill-profile"
  role = aws_iam_role.backfill.name
}
