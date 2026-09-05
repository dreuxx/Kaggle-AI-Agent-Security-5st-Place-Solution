# kaggle_evaluation

## What is `kaggle_evaluation`?

For competitions that use `kaggle_evaluation`, the hidden test set can only be accessed via `kaggle_evaluation`. This allows Kaggle to keep the hidden test set secured. Your code runs in one container. The scoring code runs in another container. This library handles the communication between them.

These competitions only provide a very limited set of error messages in order to prevent data exfiltration or data probing. We strongly encourage you to do local testing, wnich will provide complete error traces, before making a real submission.

## How to write a submission

You only need to do three things:

1. Write a function (or class) that takes data and returns predictions.
2. Create an `InferenceServer` and give it your predict function.
3. Call `server.run()`. This does the rest for you.

`server.run()` checks if this is a real competition scoring run, starts your
server, and sends your predictions back. You do not need to write that logic
yourself.

Each competition gives you an inference server class to use. Here is the minimal
pattern (replace `CompetitionInferenceServer` with the class from your
competition):

```python
import competition_inference_server  # provided by the competition


def predict(test, sample_submission):
    # Use your model to make predictions here.
    # Return predictions in the format the competition asks for.
    # The predict function signature will vary by competition.
    return sample_submission


server = competition_inference_server.CompetitionInferenceServer(predict)
server.run()
```

Note: the exact imports change for each competition. Always check the competition's starter notebook.

## How to Test Locally

Before you submit, test your code on the example data. Pass the directory that
contains the example files to `run()` with `competition_data_folder`:

```python
server.run(competition_data_folder='/path/to/competition_data/')
```

Local testing shows you the full error messages and the full traceback. The real
competition scoring run does NOT show full error messages (see "Why error
messages are limited" below). So always test locally first.

## Common Errors and What They Mean

### "Submission scoring failed"

For security, we limit the information shown in error messages. The hidden test data is only seen by the scoring system. Detailed error messages could let participants learn things about that data. That would not be fair to other participants. So the message you see is short on purpose.

To see the full error message, test on your own machine with:
 ```inference_server.run(competition_data_folder='/local_path/to/competition_data/')```
The exact file inputs will vary by competition.

### "Server never started" or connection errors

Your code must start the inference server within the startup time limit. This limit is usually 15 minutes. Common causes:

- Your code crashes during startup.
- `inference_server.run()` is never called.

### "Submission CSV not found"

The scoring system could not find your output file. Make sure your code writes the output file in the expected place with the expected name.

### Timeout

Your code took too long to finish. Check the competition page for the time limits. Try to make your model smaller or faster.

### "Server raised an exception"

Your code crashed while it was running. Test on your own machine to see the full error message.

## Tips

- Always fork the competition's starter notebook as your starting point.
- Test on your own machine before you submit.
- Check the competition's discussion forum. Other participants may have solved the same problem.
