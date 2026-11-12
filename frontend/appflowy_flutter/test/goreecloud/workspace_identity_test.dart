import 'package:appflowy/goreecloud/workspace_identity.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('GoreeCloud client display identity remains stable', () {
    expect(goreeCloudWorkspaceDisplayName, 'GoreeCloud Knowledge Workspace');
  });
}
