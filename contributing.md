# How to Contribute

We welcome contributions of all types and from people of all backgrounds to make CITAM more robust and useful to the community.

* [Code of Conduct](#code-of-conduct)
* [Questions and Problems](#questions-and-problems)
* [Submitting Issues](#submitting-issues)
* [Contributing to the Documentation](#contributing-to-the-documentation)
* [Contributing Code](#contributing-code)
* [Pull Request Guidelines](#pull-request-guidelines)

## Code of Conduct

In submitting your questions, answers, requests, etc. to this repository, you agree to do so while keeping it as a civil, open, inclusive and friendly space for people of all skill levels and backgrounds. The full Code of Conduct will be available soon.

## Questions and Problems

If you need help using CITAM or have a general question, please make sure that your question hasn't been answered before by looking at the list of [closed and open issues](https://github.com/corning-incorporated/citam/issues) and if not, describe the problem by [creating a new issue](https://github.com/corning-incorporated/citam/issues/new/choose) .

## Submitting Issues

If you found a bug (or other issues like typo in the documentation) or if you want to request a new feature, please start by reviewing [current issues](https://github.com/corning-incorporated/citam/issues) on the GitHub repository to make sure someone else hasn't already captured the same issue or requested the same feature. If not, please [submit a new issue](https://github.com/corning-incorporated/citam/issues/new/choose) with enough details for other people to reproduce the bug and/or fully understand your feature request.

Huge bonus point, if you can fix the problem or implement the feature yourself and submit a pull request to include your contributions to the CITAM repository! [This document](developers.md) has all you need to get started with contributing code.

## Contributing to the Documentation

If you find a typo in the documentation or have an idea on how to make it better, feel free to [submit a new issue](https://github.com/corning-incorporated/citam/issues/new/choose) or even better, submit a pull request with your changes.

## Contributing Code

We have a separate [developer document](developers.md) with all you need to get started with contributing code.


## Pull Request Guidelines

Please start by following all guidelines in the [developer document](developers.md) and make sure your changes are in a new git branch before you start to code. You can create a new branch with the following command where my-fix-branch should be a descriptive name of what you will be working on:

```
git checkout -b my-fix-branch dev
```

Please note that each pull request should solve one issue.

Before you start working, create a new issue describing what you will be working on or comment on an existing issue and let the community know what you will be contributing to avoid duplicate efforts. For major changes, make sure a maintainer is on board with your proposed changes before implementation.

While you work on your fix, make sure you create appropriate test cases, you follow all coding rules and you add appropriate entries to the documentation.

When you are done with your work, make sure all tests successfully pass locally on your machine. In addition, we recommend using `flake8` and `black` to catch and fix all styling problems. From within the main citam folder, you can run.

```
$pytest
$flake8
$black citam
```

If everything looks good, push your changes to GitHub:

```
$git push origin my-fix-branch
```

You are now ready to create a pull request against the dev branch. Make sure your title and description are as descriptive as poosible.

After you submit your pull request, monitor the continuous integration tests to make sure they all pass. If there is any issues, consult the log files and fix them.

Once all tests pass, a reviewer will take a look at your code and suggest any necessary changes. Implement them and push your changes to the "my-fix-branch" to automatically update your pull request.

When everything looks good, a maintainer will approve the pull request and you are done! Thanks for contributing!
